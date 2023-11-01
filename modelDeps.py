#!/bin/python3
#!/bin/python3
import pathlib
import os
import re
import argparse
from drawDeps import drawModels
from Model import Model

project_path = ""

ignorelist = ["test", "org.modellwerkstatt"]

sortweights = dict()
sortweights[".unit."] = 10
sortweights[".inout."] = 20
sortweights[".domain."] = 30
sortweights[".extern."] = 40
sortweights[".basis."] = 50
sortweights[".tecinfra."] = 50


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
        exit
    files = pathlib.Path(inDir).rglob('*.mps')
    return files


def findModels(path):
    dep_pattern = "<import index.* ref=\"(.*)\(([\w\.]*)\).* />$"
    model_pattern = "<model ref=\"(.*)\((.*)\).*>$"
    models = dict()
    mpsfiles = get_mps_files(path)
    for filepath in mpsfiles:
        mpsfile = open(filepath, "r")
        model = Model()
        for line in mpsfile:
            depmatch = re.search(dep_pattern, line)
            modelmatch = re.search(model_pattern, line)
            depModel = None
            # Find Model
            if modelmatch and modelmatch.group(1):
                modref = modelmatch.group(1)
                if modref in models:
                    model = models[modref]
                    model.isProjectModel = True
                if modref not in models:
                    model = Model()
                    model.ref = modref
                    models[model.ref] = model
                    if len(modelmatch.groups()) > 1:
                        model.name = modelmatch.group(2)
            # find outgoing dependendcies 
            if depmatch and depmatch.group(1):
                depref = depmatch.group(1)
                if depref in models:
                    depModel = models[depref]
                else:
                    depModel = Model()
                    depModel.ref = depref
                    depModel.isProjectModel = False
                    if len(depmatch.groups()) > 1:
                        depModel.name = depmatch.group(2)
                    models[depref] = depModel
                model.outgoing_deps.append(depModel)

    return models


def filterModels(models):
    filtered_models = dict()
    for model in models.values():
        if isToIgnore(model.name):
            model.isToIgnore = True
            continue
        deps = []
        for dep in model.outgoing_deps:
            if isToIgnore(dep.name):
                dep.isToIgnore = True
                continue
            deps.append(dep)
        model.outgoing_deps = deps
        filtered_models[model.ref] = model
    return filtered_models


def printModelsAsString(models):
    for model1 in models.values():
        if model1.isProjectModel:
            print(f'Model {model1.name} - Weight {model1.weight}')
            for dep in model1.outgoing_deps:
                print(f'\tdepends on {dep.name}')

def printModelNamesOnly(models):
    for model1 in models.values():
        if model1.isProjectModel:
            print(f'{model1.name} - {model1.weight}')


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
            if len(items) > 1 and items[1].lstrip("-").isdigit():
                value = items[1]
                print(f'Add "{key}={value}" to sortweights for sorting')
                sortweights[key] = int(value)

    return project_path


def sortModels(models):
    sorted_by_name = dict(sorted(models.items(),
                                 key=lambda x: x[1].name))
    sorted_nodes = dict(sorted(sorted_by_name.items(),
                               key=lambda x: x[1].weight))
    return sorted_nodes


def addWeights(models):
    categories = list(sortweights.keys())
    for model in models.values():
        for category in reversed(categories):
            if category in model.name:
                model.weight += sortweights[category]


def main():
    parser = init_argparse()
    project_path = parseArguments(parser)
    models = findModels(project_path)
    printModelsAsString(models)
    filtered_models = filterModels(models)
    addWeights(models)
    sorted_models = sortModels(filtered_models)
    printModelNamesOnly(sorted_models)
    drawModels(sorted_models)


if __name__ == "__main__":
    main()
