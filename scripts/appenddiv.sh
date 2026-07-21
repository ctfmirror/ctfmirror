#!/bin/bash

NEW_DIV='<div style="padding:3px; background:#aea9f5; font-family: arial; font-size: 20px; text-align: center;"><hr><a href="/"><img src="/assets/mirror.png"></img><h1>ctfmirror</h1>click to go main site</a><hr></div>'

ESCAPED_DIV=$(printf '%s\n' "$NEW_DIV" | sed -e 's/[\/&]/\\&/g' -e '$!s/$/\\/')

find /pingu/ctfmirror/writeups -name "index.html" -type f -exec sed -i "1i $ESCAPED_DIV" {} \;

echo "ok"
