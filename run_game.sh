#!/bin/bash
set -e
trap finish INT

PROGS=()
finish() {
    kill -9 ${PROGS[*]}
}

MAP=$1
MODEL=$2
BASE_MODEL=$3
MAX_PLAYERS=2
SEED=$4

declare -A map_to_players
map_to_players["s1"]=1
map_to_players["s3"]=1
map_to_players["d1"]=2
map_to_players["d2"]=2
map_to_players["c1"]=4
map_to_players["c2"]=4
map_to_players["c3"]=6
map_to_players["c1_wo_coop"]=4
map_to_players["c2_wo_coop"]=4
map_to_players["c3_wo_coop"]=6

if [[ -v "map_to_players[$MAP]" ]]; then
    MAX_PLAYERS=${map_to_players[$MAP]}
fi
echo "MAX_PLAYERS: $MAX_PLAYERS"

SERVER_CMD="python -m battle_city.server_sync  --turn-off-after-end --hidden-window --map $MAP --seed $SEED"
CMD_A="python -m battle_city.examples.client  --sync --model $MODEL"
CMD_B="python -m battle_city.examples.client  --sync --model $BASE_MODEL"
CMDS=(- "$CMD_A" "$CMD_B" "$CMD_B" "$CMD_B" "$CMD_B" "$CMD_B")

# decide CMDS acoording to MAP, s1, s3; d1, d2; c1, c2, c3
case $MAP in
    "s1")
        CMDS=(- "$CMD_A")
        ;;
    "s3")
        CMDS=(- "$CMD_A")
        ;;
    "d1")
        CMDS=(- "$CMD_A" "$CMD_A")
        ;;
    "d2")
        CMDS=(- "$CMD_A" "$CMD_B")
        ;;
    "c1")
        CMDS=(- "$CMD_A" "$CMD_B" "$CMD_A" "$CMD_B")
        ;;
    "c2")
        CMDS=(- "$CMD_A" "$CMD_B" "$CMD_B" "$CMD_B")
        ;;
    "c3")
        CMDS=(- "$CMD_A" "$CMD_B" "$CMD_B" "$CMD_A" "$CMD_B" "$CMD_B")
        ;;
    "c1_wo_coop")
        CMDS=(- "$CMD_A" "$CMD_B" "$CMD_A" "$CMD_B")
        ;;
    "c2_wo_coop")
        CMDS=(- "$CMD_A" "$CMD_B" "$CMD_B" "$CMD_B")
        ;;
    "c3_wo_coop")
        CMDS=(- "$CMD_A" "$CMD_B" "$CMD_B" "$CMD_A" "$CMD_B" "$CMD_B")
        ;;
    *)
        echo "Unknown MAP value: $MAP"
        exit 1
        ;;
esac

# print the cmds array to verify the result
echo "Commands for MAP=$MAP:"
printf '%s\n' "${cmds[@]}"


echo "^C to cancel..."
echo $SERVER_CMD
$SERVER_CMD&
PROGS+=($!)
sleep 1.75

i=1
while [ $i -le $MAX_PLAYERS ]; do
    sleep 1.2
    echo ${CMDS[$i]}
    ${CMDS[$i]} | sed "s/^/CLIENT $i: /"&
    PROGS+=($!)
    ((i++))
done

echo pids: $PROGS

for pid in ${PROGS[*]}; do
    wait $pid
done
