#!/bin/bash
cd ~/bachelorarbeit/data/reverse-captcha-llamacpp
MODEL_DIR="qwen3-30b-a3b"

for phase in phase1_original phase2a_enhanced phase2b_answeronly; do
  case $phase in
    phase1_original)    script=eval_phase1.py ;;
    phase2a_enhanced)   script=eval_phase2a.py ;;
    phase2b_answeronly) script=eval_phase2b.py ;;
  esac
  echo ""
  echo "=========================================="
  echo "  Starte $phase - $(date)"
  echo "=========================================="
  python3 $MODEL_DIR/$script 2>&1 | tee $MODEL_DIR/logs/${phase}.log
  echo "=== $phase fertig - $(date) ==="
done
echo ""
echo "=========================================="
echo "  Alle Phasen abgeschlossen - $(date)"
echo "=========================================="
