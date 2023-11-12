#!/bin/python3
#!/bin/python3
import pathlib
import os
import re
import argparse
from drawDeps import drawModels
from Model import Model

project_path = ""

ignorelist = ["JDK",".test", "org.modellwerkstatt", "at.hafina.basis"]
includelist = []

sortweights = dict()


def isToIgnore(name):
    for substring in ignorelist:
        if substring in name:
            return True
    return False

def isToInclude(name):
    for substring in includelist:
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


def createModel(modelref):
    model = Model()
    model.ref = modelref
    model.name = getName(modelref)
    print(f'Create: {model.name}\n\t{modelref}')
    return model


def getName(modelref):
    modelname = modelref
    name_pattern = ".*\(([a-zA-Z.\/]*)\)"
    namematch = re.search(name_pattern, modelref)
    if namematch and namematch.group(1):
        modelname = namematch.group(1)
        if("/" in modelname):
            parts = modelname.split("/")
            if parts[1]: 
                modelname = parts[1]
            else: 
                modelname = parts[0]
    return modelname


def findModels(path):
    dep_pattern = \
        "<import index=\"[a-zA-Z0-9]*\" ref=\"([^\s]+)\" .*\/>"
    model_pattern = "<model ref=\"(.*)\">"
    models = dict()
    mpsfiles = get_mps_files(path)
    for filepath in mpsfiles:
        mpsfile = open(filepath, "r")
        # # print(filepath)
        model = Model()
        for line in mpsfile:
            depmatch = re.search(dep_pattern, line)
            modelmatch = re.search(model_pattern, line)
            depModel = None
            # Find Model
            if modelmatch and modelmatch.group(1):
                modref = modelmatch.group(1)
                # if isToIgnore(modref): 
                #     continue
                if modref in models:
                    model = models[modref]
                    model.isProjectModel = True
                else:
                    model = createModel(modref)
                    models[model.ref] = model
                    model.isProjectModel = True
            # find outgoing dependendcies 
            if depmatch and depmatch.group(1):
                depref = depmatch.group(1)
                if depref in models:
                    depModel = models[depref]
                else:
                    depModel = createModel(depref)
                    depModel.isProjectModel = False
                    models[depref] = depModel
                model.outgoing_deps.append(depModel)
                depModel.incoming_deps.append(model)

    return models


def getCommonSubstring(models):
    common = ""
    for modeli in models.values():
        if not common:
            common = modeli.name
        else:
            common = findLongestSubstring(common, modeli.name)
    return common


def shortenModelnames(models):
    common_substring = getCommonSubstring(models)
    if common_substring:
        for model in models.values():
            parts = model.name.split(common_substring)
            if len(parts) > 1: 
                newname = parts[1]
                model.name = newname



def findLongestSubstring(str1, str2):
    result = ""
    for i in range(0, min(len(str1),len(str2))):
        if str1[i] == str2[i]:
            result += str1[i]
        else:
            return result
    return result


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
        if len(includelist) > 0:
            if isToInclude(model.name): 
                filtered_models[model.ref] = model
        else:
            filtered_models[model.ref] = model
    return filtered_models


def printModelsAsString(models):
    for model1 in models.values():
        if "KontrolleUI" in model1.name:
            if model1.isProjectModel:
                print(f'Model {model1.name} - Weight {model1.weight}')
                print(f'\t{len(model1.outgoing_deps)} outgoing ')
                print(f'\t{len(model1.incoming_deps)} incoming ')
                print(f'\tInstability: {round(model1.getInstability(),2)}')
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
    parser.add_argument('--include', nargs='*',
                        help='list of (sub)string to consider')
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
    if args.include:
        for x in args.include:
            print(f'Adding "{x}" to Includelist')
            includelist.append(x)
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
    sorted_nodes = models
    sorted_nodes = dict(sorted(
        sorted_nodes.items(),
        key=lambda x: len(x[1].outgoing_deps),
        reverse=True))
    sorted_nodes = dict(sorted(
        models.items(),
        key=lambda x: len(x[1].incoming_deps),
        reverse=True))
    # sorted_by_name = dict(sorted(models.items(),
    #                              key=lambda x: x[1].name))
    sorted_nodes = dict(sorted(
        sorted_nodes.items(),
        key=lambda x: x[1].getInstability(),
        reverse=True))
    sorted_nodes = dict(sorted(sorted_nodes.items(),
                               key=lambda x: x[1].weight, reverse=False))
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
    shortenModelnames(sorted_models)
    # printModelNamesOnly(sorted_models)
    printModelsAsString(sorted_models)
    drawModels(sorted_models)


if __name__ == "__main__":
    main()
