set -eu
xrandr --query | grep -A 1 connected | grep -v connected | grep -v '\-\-' | awk '{print $1}' | head -1
