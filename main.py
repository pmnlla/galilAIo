import argparse
import sys, os, time
import subprocess

def check_deps(args):
    print("Checking dependencies...")
    deps_present = True
    if not args.npm:
        try:
            subprocess.run(['bun', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print("Bun is not installed. Please install Bun from https://bun.sh/.")
            print("hint: you can pass --npm to use npm instead of bun, but bun is recommended. Deno who?")
            deps_present = False
    else:
        try:
            subprocess.run(['npm', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print("npm is not installed. Please install npm from https://www.npmjs.com/get-npm.")
            deps_present = False
    try:
        subprocess.run(['uv', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("uv is not installed. Please install uv from https://astral.sh. It is mandatory for running galilaio-visiond.")
        deps_present = False
    return deps_present

def gallilaio_init(args):
    print("Initializing Galilaio...")
    # Add initialization code here
    if not check_deps(args):
        print("Please install the missing dependencies and try again.")
        exit(1)
    
    os.chdir('core')
    if not args.npm:
        subprocess.run(['bun', 'i'], check=True)
    else:
        subprocess.run(['npm', 'i'], check=True)
    
    os.chdir('../vision')
    subprocess.run(['uv', 'sync'], check=True)
    
    print("Initialization complete. Please configure your .env file in the core directory")

def gallilaio_run(args):
    print("Running Galilaio...")
    if not args.npm:
        proc_js = subprocess.Popen(['bunx','next', 'dev', '--turbo', '-v' if args.verbose else ''], cwd="core")
    else:
        proc_js = subprocess.Popen(['npm', 'run', 'dev'], cwd="./core")
    proc_vision = subprocess.Popen(['uv', 'run', 'fastapi', 'dev'], cwd="./vision")

    while True:
        True
    
    proc_vision.kill()
    proc_js.kill()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Galilaio utility script")
    parser.add_argument("--init", help="Initialize this deployment of Gallilaio. Does not handle environment configuration.", type=bool, required=False)
    parser.add_argument("--run", help="Run Galilaio", type=bool, required=False)
    parser.add_argument("--verbose", help="Run Galilaio with verbosity", type=bool, required=False)
    parser.add_argument("--npm", help="Use npm instead of bun - not recommended ૮꒰ ˶• ༝ •˶꒱ა ♡", type=bool, required=False)
    args = parser.parse_args()

    if args.init:
        gallilaio_init(args)
    if args.run:
        gallilaio_run(args)
