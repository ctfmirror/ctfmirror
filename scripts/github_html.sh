#!/bin/bash

TARGET_DIR="/pingu/ctfmirror/writeups"

find "$TARGET_DIR" -name "*.html" -type f | while read -r html_file; do
    
    if grep -qE "githubassets|github\.com|github-markdown" "$html_file"; then
        echo "found: $html_file"
        sed -i -e '/<script/,/<\/script>/d' "$html_file"
        sed -i -e 's/<script[^>]*\/>//g' "$html_file"
        echo "stripped js tags from: $html_file"
    fi
done
echo "ok"
