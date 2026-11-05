"""Manual lab-only v2 runner; never uses ADB to send keys.

Upstream TLS disables server verification. This is not a production secure adapter.
"""
import argparse
import asyncio
import datetime
import getpass
import json
import logging
from pathlib import Path

KEYS = {"up": "DPAD_UP", "down": "DPAD_DOWN", "left": "DPAD_LEFT", "right": "DPAD_RIGHT"}


def key_for(command):
    return KEYS[command]  # strict allowlist: no enter/home/power/shell/text


def emit(event, **fields):
    print(json.dumps({"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      "event": event, **fields}), flush=True)


async def run(args):
    from androidtvremote2 import AndroidTVRemote
    logging.disable(logging.CRITICAL)  # upstream debug may include pairing code
    args.identity.mkdir(parents=True, exist_ok=True)
    remote = AndroidTVRemote("Marco G0 lab", str(args.identity/"client.pem"),
                             str(args.identity/"client.key"), args.host,
                             enable_ime=False, enable_voice=False)
    try:
        await remote.async_generate_cert_if_missing()
        if args.pair:
            emit("pair_start_attempt")
            await asyncio.wait_for(remote.async_start_pairing(), 15)
            emit("pair_configuration_ack", meaning="not_yet_paired")
            code = await asyncio.to_thread(getpass.getpass, "TV six-character hex code (hidden): ")
            await asyncio.wait_for(remote.async_finish_pairing(code.strip()), 15)
            code = None
            emit("pair_secret_ack")
        await asyncio.wait_for(remote.async_connect(), 15)
        emit("session_ready", meaning="protocol_handshake_only")
        while True:
            command = (await asyncio.to_thread(input, "up/down/left/right, reconnect, quit: ")).strip().lower()
            if command == "quit":
                break
            if command == "reconnect":
                remote.disconnect()
                emit("local_disconnect")
                await asyncio.sleep(2)
                await asyncio.wait_for(remote.async_connect(), 15)
                emit("reconnected", meaning="same_client_identity_protocol_only")
            elif command in KEYS:
                remote.send_key_command(key_for(command))
                emit("key_queued", direction=command, meaning="not_device_execution_ack")
                observation = (await asyncio.to_thread(input, "Did TV focus visibly move? yes/no/unknown: ")).strip()
                emit("human_observation", direction=command,
                     result=observation if observation in ("yes", "no", "unknown") else "unknown")
            else:
                emit("command_rejected")
    except Exception as error:
        emit("failed", error_type=type(error).__name__,
             cause_type=type(error.__cause__).__name__ if error.__cause__ else None)
        return 1
    finally:
        remote.disconnect()
        emit("local_disconnect_finally")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--identity", required=True, type=Path, help="Private per-TV directory; never commit")
    parser.add_argument("--pair", action="store_true")
    parser.add_argument("--accept-lab-unverified-server", action="store_true")
    args = parser.parse_args()
    if not args.accept_lab_unverified_server:
        parser.error("Lab-only upstream CERT_NONE requires --accept-lab-unverified-server")
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
