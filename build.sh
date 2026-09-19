#!/bin/bash -eu

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -e . pyinstaller

for fuzzer in $(find "$SRC/fuzzers" -name '*_fuzzer.py'); do
  fuzzer_basename=$(basename -s .py "$fuzzer")
  pyinstaller --distpath "$OUT" --onefile --name "${fuzzer_basename}.pkg" "$fuzzer"
  cat > "$OUT/$fuzzer_basename" <<EOF
#!/bin/sh
this_dir=\$(dirname "\$0")
"\$this_dir/${fuzzer_basename}.pkg" "\$@"
EOF
  chmod +x "$OUT/$fuzzer_basename"
done
