#!/usr/bin/env python

import sys
import argparse

from netCDF4 import Dataset

def main(args):
    dsin = Dataset(args.infile)
    dsout = Dataset(args.outfile, 'w')

    # Copy global attributes
    for att in dsin.ncattrs():
        dsout.setncattr(att, dsin.getncattr(att))

    # Determine variables to copy
    if args.variable:
        if not set(args.variable).issubset(set(dsin.variables.keys())):
            raise AssertionError('Specified variables are not available in the input file')
        vars_to_copy = set(args.variable)
        
        # Vars as exclusion list?
        if args.exclude:
            vars_to_copy = set(dsin.variables.keys()).difference(vars_to_copy)
    else:
        vars_to_copy = dsin.variables.keys()

    # Determine dimensions to copy
    dims_to_copy = set()
    for v in vars_to_copy:
        dims_to_copy = dims_to_copy.union(set(dsin.variables[v].dimensions))
    # Add associate dimvars (Assumes dimvars have same name as dimension)
    if not all([x in dsin.variables.keys() for x in dims_to_copy]):
        raise AssertionError('Not all dimenions being copied have associated dimension variables')

    print 'Copying variables: {}'.format(vars_to_copy)
    print 'Copying dimensions: {}'.format(dims_to_copy)

    # Copy Dimensions
    for dname, dim in dsin.dimensions.items():
        if dname not in dims_to_copy:
            continue
        print dname, len(dim)
        dsout.createDimension(dname, len(dim) if not dim.isunlimited() else None)

    # Copy Variables
    for v_name, varin in dsin.variables.items():
        if v_name not in vars_to_copy:
            continue
        outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
        print v_name, varin.datatype, varin.dimensions, varin.shape, len(varin.shape)

        # Copy all variable attributes
        outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})

        # Itteratively write variables with 3+ dimensions
        if len(varin.shape) > 2:
            count = float(varin.shape[0])
            for i in range(varin.shape[0]):
                if args.progress: 
                    sys.stdout.write("\r{:.2%}".format(i/count))
                outVar[i,:,:] = varin[i,:,:]
        else:
            outVar[:] = varin[:]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='Input file name')
    parser.add_argument('outfile', help='Output file name')
    parser.add_argument('-v', '--variable', nargs= '+',  help='Variable(s) to include in output. Ex: -v var1 var2 var3')
    parser.add_argument('-x', '--exclude', default=False, action='store_true', help='Excludes listed variables')
    parser.add_argument('--progress', default=False, action='store_true', help='Display percentage progress')
    args = parser.parse_args()

    main(args)
