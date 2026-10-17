#!/bin/bash
cd ~/bachelorarbeit/data/reverse-captcha-llamacpp
for phase in phase2a_enhanced phase2b_answeronly; do
  case $phase in
    phase2a_enhanced)   script=eval_phase2a.py ;;
    phase2b_answeronly) script=eval_phase2b.py ;;
  esac
  echo "=== $phase - $(date) ==="
  python3 qwen3-30b-a3b/$script 2>&1 | tee qwen3-30b-a3b/logs/${phase}_v2.log
done
