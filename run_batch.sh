# model list
models=("glm4-9b" "yi-9b" "int-7b" "qwen2-7b" "llama3-8b" "mistral-7b" "gemma2-9b")
# models=("gpt4om" "gpt3.5")

base_model="yi-9b"

# scenario list
scenarios=("s1" "s3" "d1" "d2" "c1" "c2" "c3")
# scenarios=("c1_wo_coop" "c2_wo_coop" "c3_wo_coop")

# random seed list
seeds=(1 2 3 4 5)

# iterate through model list
for model in "${models[@]}"; do
    echo "Running tests for model: $model"
    
    # iterate through scenario list
    for scenario in "${scenarios[@]}"; do

        # iterate through seed list
        for seed in "${seeds[@]}"; do
            echo "  Running scenario: $scenario"
            bash ./run_game.sh "$scenario" "$model" "$base_model" "$seed"
        done
    done
    
    echo "Completed tests for model: $model"
    echo
done

echo "All tests completed."