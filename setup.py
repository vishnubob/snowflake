#!/usr/bin/env python

from distutils.core import setup, Extension

snowflake = {
    "name":"snowflake",
    "description":"snowflake generator",
    "author":"Giles Hall / Rachael Holmes",
    "packages": ["sfgen"],
    "package_dir": {
                    "sfgen": "src", 
                    },
    "py_modules":[
                    "sfgen.__init__", 
                    "sfgen.curves", 
                    "sfgen.splines", 
                ],
    "scripts":[
                "scripts/snowflake.py",
               ],
    "version": "0.3",
}

if __name__ == "__main__":
    setup(**snowflake)
