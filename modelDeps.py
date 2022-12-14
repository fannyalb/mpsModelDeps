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
            dep = None
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
            # find Deps
            if depmatch and depmatch.group(1):
                depref = depmatch.group(1)
                if depref in models:
                    dep = models[depref]
                else:
                    dep = Model()
                    dep.ref = depref
                    dep.isProjectModel = False
                    if len(depmatch.groups()) > 1:
                        dep.name = depmatch.group(2)
                    models[depref] = dep
                model.deps.append(dep)

    return models


def filterModels(models):
    filtered_models = dict()
    for model in models.values():
        if isToIgnore(model.name):
            continue
        deps = []
        for dep in model.deps:
            if isToIgnore(dep.name):
                continue
            deps.append(dep)
        model.deps = deps
        filtered_models[model.ref] = model
    return filtered_models


def printModelsAsString(models):
    for model1 in models.values():
        if model1.isProjectModel:
            print(f'Model {model1.name} - Weight {model1.weight}')
            for dep in model1.deps:
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
                        help='Liste von (sub)Strings (Packagenamensteile) \
                                die zu ignorieren sind (models or deps) \
                                z.B. --ignore modellwerkstatt'
                        )
    parser.add_argument('--sort', nargs='*',
                        metavar="KEY=VALUE",
                        help='Liste von Packagenamensteilen mit Gewichten, \
                              nach denen sortiert wird \
                              Gewichte werden addiert! \
                                e.g. "--sort inout=10 akteur=6 benutzer=-3"')
    parser.add_argument('--clearsort',
                        action="store_true",
                        help='Aktuelle Sortiergewichte loeschen')
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
    if args.sort:
        for kv in args.sort:
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
    filtered_models = filterModels(models)
    addWeights(models)
    sorted_models = sortModels(filtered_models)
    printModelNamesOnly(sorted_models)
    drawModels(sorted_models)


if __name__ == "__main__":
    main()
