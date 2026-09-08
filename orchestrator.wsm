(def mcp-path "/home/agents/GitHub/vault-semantic-mcp/")

(def apply-semantic-tags
  (lambda ()
    (print "1. GPU-NLP...")
    (process-run "bash" (list "-c" (string-append "export OMP_NUM_THREADS=2 && export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True && /home/agents/GitHub/FlagEmbedding/.venv/bin/python " (string-append mcp-path "classify_corpus_semantic.py"))))
    
    (print "2. Tag Applier...")
    (process-run "/home/agents/GitHub/FlagEmbedding/.venv/bin/python" (list (string-append mcp-path "apply_tags.py")))
    
    (print "Done!")))

(apply-semantic-tags)
