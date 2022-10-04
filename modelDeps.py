#!/bin/python3
import pathlib
import os
import re
import glob
import argparse
from drawDeps import drawDeps

project_path = ""

ignorelist = ["test", "org.modellwerkstatt"]

sortweights = dict()
sortweights[".unit."] = 100
sortweights[".inout."] = 200
sortweights[".domain."] = 300
sortweights[".extern."] = 400
sortweights[".basis."] = 450
sortweights[".tecinfra."] = 500


def isToIgnore(name):
    for substring in ignorelist:
        if substring in name:
            return True
    return False


def sortweightsPrinted():
    output = ''
    for substring in sortweights:
        output += f'\t"{substring}" = {sortweights[substring]}\n'
    output += '\t DEFAULT = 50'
    return output


def get_mps_files(inDir):
    print(f'Get mspfiles from {inDir}')
    if not inDir.is_dir():
        print(f'{inDir} is not a Dir!')
        exit
    # files = glob.glob(os.path.join(inDir, '*.mps'), recursive=True)
    files = pathlib.Path(inDir).rglob('*.mps')
    print(files)
    return files


def find_model_deps(path):
    dep_pattern = "<import index.*\(([\w\.]*)\).* />$"
    model_pattern = "<model.*\((.*)\).*>$"
    model_deps = dict()
    mpsfiles = get_mps_files(path)
    for filepath in mpsfiles:
        filename = os.path.basename(filepath)
        deps = set()
        mpsfile = open(filepath, "r")
        model = filename[:-4]
        for line in mpsfile:
            depmatch = re.search(dep_pattern, line)
            modelmatch = re.search(model_pattern, line)
            if depmatch and depmatch.group(1):
                deps.add(depmatch.group(1))
            if modelmatch and modelmatch.group(1):
                model = modelmatch.group(1)
        model_deps[model] = deps
    return model_deps


def filterModelDeps(model_deps):
    filtered_deps = dict()
    for model in model_deps:
        if isToIgnore(model):
            continue
        deps = set()
        for dep in model_deps[model]:
            if isToIgnore(dep):
                continue
            deps.add(dep)
        filtered_deps[model] = deps
    return filtered_deps


def printModelDepsAsString(model_deps):
    for model in model_deps:
        print(f'Model {model} depends on:')
        for dep in model_deps[model]:
            print(f'\t{dep}')


def init_argparse() -> argparse.ArgumentParser:
    sortweightsprint = sortweightsPrinted()
    epilog_text = f'''
        current sortweights:
        {sortweightsprint}
        current ignorelist:
            {ignorelist}'''
    parser = argparse.ArgumentParser(prog='modelDeps',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog_text)
    parser.add_argument('--path', nargs=1,
                        required=True,
                        type=pathlib.Path,
                        help='path to MPS-models')
    parser.add_argument('--ignore', nargs='*',
                        help='list of (sub)strings to ignore (models or deps)'
                        )
    parser.add_argument('--sortby', nargs='*',
                        metavar="KEY=VALUE",
                        help='list of (substrings) and weigths to sort by.  \
                                e.g. "inout=10"')
    parser.add_argument('--clearsort',
                        action="store_true",
                        help='Clear current sortweights')
    return parser


def parseArguments(parser):
    args = parser.parse_args()
    if args.path:
        project_path = args.path[0]
        print(f'Project path now: {project_path}')
    if args.ignore:
        for x in args.ignore:
            print(f'Adding "{x}" to Ignorelist')
            ignorelist.append(x)
    if args.clearsort:
        print('Deleting default sortweights....')
        sortweights.clear()
    if args.sortby:
        for kv in args.sortby:
            items = kv.split('=')
            key = items[0].strip()
            if len(items) > 1 and items[1].isdigit():
                value = items[1]
                print(f'Add "{key}={value}" to sortweights for sorting')
                sortweights[key] = int(value)

    return project_path


def sortFunc(modelname):
    categories = list(sortweights.keys())
    for category in reversed(categories):
        if category in modelname:
            return sortweights[category]
    return 50


def sortModelDeps(model_deps):
    sorted_nodes = dict(sorted(model_deps.items(),
                               key=lambda x: sortFunc(x[0])))
    return sorted_nodes


def main():
    parser = init_argparse()
    project_path = parseArguments(parser)
    model_deps = find_model_deps(project_path)
    filtered_deps = filterModelDeps(model_deps)
    sorted_deps = sortModelDeps(filtered_deps)

    drawDeps(sorted_deps)


if __name__ == "__main__":
     main()
