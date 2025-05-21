#!/usr/bin/env python3
import os
import json
import argparse
import shutil
from textwrap import indent

CONSUL_URL = "http://157.159.160.197:8500"

APP_TEMPLATE = """\
#####################################
# Handles incoming and outgoing connections
#####################################
import time
import logging
import numpy as np
from node import Node
from queue import Queue
from itertools import count as _count

# If there’s a custom Content in add_files/<module>.py, we’ll import it below
{custom_import}

if __name__ == "__main__":
    # --- Logging setup ---
    log_file_path = "/app/logs/container.log"
    CONSUL_URL='{CONSUL_URL}'

    # --- A counter for naming output variables ---
    _var_counter = _count(1)
    
    # --- Instantiate your custom logic (if any) ---
{content_init}
    in_q = Queue()

    def handle_msg(creds, var_name, msg, node_obj):
        # push into our local queue
        in_q.put((creds, var_name, msg))
        # if content wants data, wait until at least one batch is in
        if content.requires_data:
            while in_q.empty():
                time.sleep(0.1)
            _, _, latest = None, None, None
            while not in_q.empty():
                _, _, latest = in_q.get()
            out = content.run(latest)
        else:
            out = content.run()

        # send the result right away
        idx = next(_var_counter)
        send_payload = {{"var_handle_msg{{}}".format(idx): out}}
        node_obj.send_data_to_peers(send_payload)
        # reset sent_peers so we can re-send if needed:
        # node_obj.sent_peers.clear()

    # --- Build the Node, give it your role, device, etc. ---
    if content.requires_data :
        receive_logic = {receive_logic}
    else :
        receive_logic=None
    # receive_logic=None

    node = Node(
        5000,
        log_file_path=log_file_path,
        container_name="{module}",
        role="{role}",
        device="{device}",
        consul_url=CONSUL_URL,
        target_roles={targets},
        on_receive=receive_logic,
    )

    # --- Decide if we wait for incoming data before running ---
{run_block}

    while True:
        time.sleep(1)
"""

#     # --- Send whatever came back from run() as your send_data dict ---
#     node.send_data_to_peers(send_data=send_data)

#     # --- Optional: keep alive if you want to inspect logs, etc. ---
#     time.sleep(30)
# """

def generate_app_file(module, modules_dir, add_files_dir):
    name    = module["Name"]
    role    = module.get("Role", "default_role")
    device  = module.get("Device", "CPU")
    targets = module.get("Send_to", [])

    module_dir  = os.path.join(modules_dir, name)
    out_path    = os.path.join(module_dir, f"app_{name}.py")
    add_dest    = os.path.join(module_dir, "add_files")
    dockerfile  = os.path.join(module_dir, f"Dockerfile.{name}")

    os.makedirs(module_dir, exist_ok=True)

    # 1) Handle custom code (file or folder)
    single_py  = os.path.join(add_files_dir, f"{name}.py")
    folder_src = os.path.join(add_files_dir, name)

    if os.path.isfile(single_py):
        os.makedirs(add_dest, exist_ok=True)
        shutil.copy(single_py, add_dest)
        custom_import = f"from add_files.{name} import Content"
        content_init  = "    content = Content()"
        receive_logic = "handle_msg"
        #TODO look at the receive logic be carefule with the if isfile and elif isdir()
#         run_block = indent(
#             """\
# if content.requires_data:
#     while not node.received_data:
#         time.sleep(0.1)
#     send_data = {'var1': content.run(node.received_data)}
# else:
#     send_data = {'var1': content.run()}
# """, "    "
#         )
        run_block = indent(
            """\
if not content.requires_data:
        initial = content.run()
        node.send_data_to_peers({"var1": initial})
""", "    "
        )

    elif os.path.isdir(folder_src):
        if os.path.exists(add_dest):
            shutil.rmtree(add_dest)
        shutil.copytree(folder_src, add_dest)
        custom_import = f"from add_files.{name} import Content"
        content_init  = "    content = Content()"
        receive_logic = "handle_msg"
        # run_block = indent(
#             """\
# if content.requires_data:
#     while not node.received_data:
#         time.sleep(0.1)
#     send_data = {'var1': content.run(node.received_data)}
# else:
#     send_data = {'var1': content.run()}
# """, "    "
        # )
        run_block = indent(
            """\
if not content.requires_data:
        initial = content.run()
        node.send_data_to_peers({"var1": initial})
""", "    "
        )

    else:
        custom_import = "# (no custom add_files — using default random sender)"
        content_init  = ""
        receive_logic = "None"
        run_block = indent(
            """\
# default: send a single random 1KB-ish NumPy array under 'var1'
for i in range(10):
    send_data = {f'var{i}': 'np.random.rand(64,64).astype(float)'}
    node.send_data_to_peers(send_data)
    time.sleep(0.1)
""", "    "
        )

    # 2) If there’s a requirements.txt in the add_files folder, copy & schedule install
    req_src = None
    # either <add_files>/c1/requirements.txt or a top-level add_files/c1.txt
    for candidate in (
        os.path.join(add_files_dir, name, "requirements.txt"),
        os.path.join(add_files_dir, f"{name}.requirements.txt"),
    ):
        if os.path.isfile(candidate):
            req_src = candidate
            break

    if req_src:
        shutil.copy(req_src, os.path.join(module_dir, "requirements.txt"))
        # make sure we have a Dockerfile to patch
        if os.path.exists(dockerfile):
            with open(dockerfile, "a") as df:
                df.write("\n# install module-specific requirements\n")
                df.write("COPY requirements.txt /app/requirements.txt\n")
                df.write("RUN pip install --no-cache-dir -r /app/requirements.txt\n")
        else:
            print(f"Warning: Dockerfile not found for module {name}, cannot add requirements step.")

    # 3) Render & write the app_<name>.py
    app_py = APP_TEMPLATE.format(
        custom_import=custom_import,
        content_init=content_init,
        module=name,
        role=role,
        device=device,
        targets=targets,
        run_block=run_block,
        CONSUL_URL=CONSUL_URL,
        receive_logic=receive_logic
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"[parser_app_file] → Writing generated app to: {out_path}")

    try:
        with open(out_path, "w") as f:
            f.write(app_py)
        print(f"[parser_app_file] ✓ Successfully wrote {out_path}")
    except Exception as e:
        print(f"[parser_app_file] ✗ ERROR writing {out_path}: {e}")

    # with open(out_path, "w") as f:
    #     f.write(app_py)


def main():
    parser = argparse.ArgumentParser(description="Generate per-module app_<name>.py")
    parser.add_argument("-j", "--json",    required=True, help="Path to config.json")
    parser.add_argument("-m", "--modules", required=True,
                   help="Path to modules/ directory")
    parser.add_argument("-a", "--addfiles", required=True,
                   help="Path to add_files/ directory")
    args = parser.parse_args()

    cfg = json.load(open(args.json))
    for module in cfg.get("Modules", []):
        generate_app_file(module, args.modules, args.addfiles)
        print(f"Generated app for {module['Name']}")

if __name__ == "__main__":
    main()