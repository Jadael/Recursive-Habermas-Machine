# API Configuration Enhancement

## Overview

The Habermas Machine now supports **separate API endpoints and models** for statement generation and ranking prediction. This enhancement enables:

1. **Multi-provider setups**: Use different LLM providers for different tasks
2. **Performance optimization**: Use faster/cheaper models for ranking, more capable models for generation
3. **OpenAI-compatible API support**: Works with any OpenAI-compatible endpoint (Ollama, LM Studio, vLLM, Together AI, etc.)

---

## New Settings (Settings Tab)

### 🔧 Statement Generation API

Configure the API used for generating consensus candidate statements:

- **API Endpoint**: Full URL to the generation endpoint
  - Default: `http://localhost:11434/api/generate` (Ollama)
  - Examples:
    - Ollama: `http://localhost:11434/api/generate`
    - LM Studio: `http://localhost:1234/v1/completions`
    - vLLM: `http://your-server:8000/v1/completions`
    - Together AI: `https://api.together.xyz/v1/completions`

- **Model**: Model name for generation
  - Default: `deepseek-r1:14b`
  - Use provider-specific model names

- **Parameters**:
  - Temperature (default: 0.7)
  - Top P (default: 0.9)
  - Top K (default: 40)
  - Candidate Statements (default: 4)

### 🎯 Ranking Prediction API

Configure the API used for predicting how participants would rank candidates:

- **API Endpoint**: Full URL to the ranking endpoint
  - Default: `http://localhost:11434/api/generate` (Ollama)
  - Can be different from generation endpoint

- **Model**: Model name for ranking
  - Default: `deepseek-r1:14b`
  - Can be different from generation model

- **Parameters**:
  - Temperature (default: 0.6 - lower for more deterministic rankings)
  - Max JSON Retries (default: 3)

---

## Use Cases

### 1. Cost Optimization
```
Generation: GPT-4 @ OpenAI (high quality)
Ranking: GPT-3.5-turbo @ OpenAI (faster, cheaper)
```

### 2. Local + Cloud Hybrid
```
Generation: deepseek-r1:14b @ Ollama (local, privacy)
Ranking: claude-3-haiku @ Anthropic API (cloud, speed)
```

### 3. Multi-GPU Setup
```
Generation: llama3.1:70b @ localhost:11434 (GPU 1)
Ranking: llama3.1:8b @ localhost:11435 (GPU 2)
```

### 4. A/B Testing Models
```
Generation: qwen2.5:14b @ Ollama
Ranking: deepseek-r1:14b @ Ollama
(Compare results with different model combinations)
```

---

## Configuration Examples

### Example 1: All Ollama (Default)
```
Generation API:
  Endpoint: http://localhost:11434/api/generate
  Model: deepseek-r1:14b
  Temperature: 0.7

Ranking API:
  Endpoint: http://localhost:11434/api/generate
  Model: deepseek-r1:14b
  Temperature: 0.6
```

### Example 2: LM Studio for Both
```
Generation API:
  Endpoint: http://localhost:1234/v1/completions
  Model: TheBloke/Mistral-7B-Instruct-v0.2-GGUF
  Temperature: 0.7

Ranking API:
  Endpoint: http://localhost:1234/v1/completions
  Model: TheBloke/Mistral-7B-Instruct-v0.2-GGUF
  Temperature: 0.6
```

### Example 3: Separate Ollama Instances
```
Generation API:
  Endpoint: http://localhost:11434/api/generate
  Model: llama3.1:70b
  Temperature: 0.7

Ranking API:
  Endpoint: http://localhost:11435/api/generate
  Model: llama3.1:8b
  Temperature: 0.6
```

### Example 4: Cloud API (Together AI)
```
Generation API:
  Endpoint: https://api.together.xyz/v1/completions
  Model: meta-llama/Llama-3-70b-chat-hf
  Temperature: 0.7

Ranking API:
  Endpoint: https://api.together.xyz/v1/completions
  Model: meta-llama/Llama-3-8b-chat-hf
  Temperature: 0.6

Note: May require API key authentication (not yet implemented)
```

---

## Technical Details

### Backward Compatibility

The legacy variables (`self.model_var`, `self.temperature_var`, etc.) now point to the new generation-specific variables for backward compatibility with existing code paths:

```python
self.model_var = self.gen_model_var  # Legacy compatibility
self.temperature_var = self.gen_temperature_var
self.ranking_temperature_var = self.rank_temperature_var
```

### Logging

Detailed output now shows both endpoints and models:

```
**Generation Model:** deepseek-r1:14b @ http://localhost:11434/api/generate
**Ranking Model:** deepseek-r1:14b @ http://localhost:11434/api/generate
```

### Code Changes

Key functions updated:

1. `generate_single_candidate()` - Uses `gen_api_endpoint_var`, `gen_model_var`, `gen_temperature_var`, etc.
2. `get_ranking_with_retries()` - Uses `rank_api_endpoint_var`, `rank_model_var`, `rank_temperature_var`
3. `apply_preset()` - Sets both generation and ranking models from presets

---

## Future Enhancements

Potential improvements for future versions:

1. **API Key Support**: Add fields for authentication headers
2. **Custom Headers**: Support for bearer tokens, custom headers
3. **Request Format Templates**: Support different API request formats (OpenAI vs Ollama vs custom)
4. **Connection Testing**: "Test Connection" buttons to verify endpoints
5. **Response Format Handling**: Better handling of different API response formats
6. **Preset Templates**: Save/load complete API configurations as presets
7. **Model Discovery**: Auto-populate available models from API endpoints

---

## Troubleshooting

### Issue: "Connection refused" error

**Solution**: Verify the endpoint is running and accessible
```bash
# For Ollama:
curl http://localhost:11434/api/generate

# For LM Studio:
curl http://localhost:1234/v1/models
```

### Issue: "Model not found" error

**Solution**: Check model name matches what's available on the server
```bash
# For Ollama:
ollama list

# For LM Studio: Check the UI
```

### Issue: Responses not streaming properly

**Solution**: Some APIs may not support streaming. Future versions may add a "stream" toggle.

---

## Migration Guide

### From Previous Version

Your existing settings will automatically migrate:
- Old `Model` field → Both generation and ranking models
- Old `Temperature` → Generation temperature
- Old `Ranking Temperature` → Ranking temperature
- Old hardcoded endpoint → Both API endpoints

No manual configuration required unless you want to use separate endpoints/models.

---

## Questions?

Check the main documentation in `CLAUDE.md` or open an issue on GitHub.
