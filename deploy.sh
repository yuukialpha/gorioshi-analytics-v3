#!/bin/bash

tmux kill-server

sleep 5

tmux new -s tunnel -d
tmux send-keys -t tunnel 'cloudflared tunnel --url http://127.0.0.1:8000 --name gorioshi' C-m

tmux new -s server -d
tmux send-keys -t server 'gunicorn app:app' C-m
