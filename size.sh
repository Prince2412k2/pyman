envs_dir=$(conda info --base)/envs
du -sb "$envs_dir"/* 2>/dev/null | awk '{printf "%-30s %10.2f MB\n", substr($2, index($2,$3)), $1/1024/1024}' | sort -k2 -h
