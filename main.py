import argparse

def check_deps(args):
    print("Checking dependencies...")
    deps_present = True
    if not args.npm:
        try:
            !bun 
        except Exception as e:
            print("Bun is not installed. Please install Bun from https://bun.sh/.")
            print("hint: you can pass --npm to use npm instead of bun, but bun is recommended. Deno who?")
            deps_present = False
    else:
        try:
            !npm 
        except Exception as e:
            print("npm is not installed. Please install Bun from https://bun.sh/.")
            deps_present = False
    try:
        !uv
    except Exception as e:
        print("uv is not installed. Please install uv from https://astral.sh. It is mandatory for running galilaio-visiond.")
        deps_present = False

def gallilaio_init(args):
    print("Initializing Galilaio...")
    # Add initialization code here
    check_deps(args)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Galilaio utility script")
    parser.add_argument("init", help="Initialize this deployment of Gallilaio. **Does not handle environment configuration**.", type=bool)
    parser.add_argument("run", help="Run Galilaio", type=bool)
    parser.add_argument("run-verbose", help="Run Galilaio with verbosity", type=bool)
    parser.add_argument("npm", help="Use npm instead of bun - not recommended ૮꒰ ˶• ༝ •˶꒱ა ♡", type=bool)
    args = parser.parse_args()

    if args.init:
        gallilaio_init()