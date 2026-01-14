"""
Wrapper sederhana untuk seq2seq generation menggunakan Hugging Face Transformers.

Module ini bersifat "best-effort":
Jika `transformers` / model belum terinstall atau gagal load,
fungsi akan melempar Exception yang bisa ditangani oleh caller.

Konfigurasi:
- ENABLE_SEQ2SEQ harus bernilai "1" agar aktif
- SEQ2SEQ_MODEL bisa diisi nama model HuggingFace (default: google/mt5-small)
"""

import os
from typing import Optional

# Cek apakah seq2seq diaktifkan
ENABLED = os.environ.get("ENABLE_SEQ2SEQ", "0") == "1"
MODEL_NAME_DEFAULT = os.environ.get("SEQ2SEQ_MODEL", "google/mt5-small")


class Seq2SeqGenerator:
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        if not ENABLED:
            raise RuntimeError("Seq2Seq disabled. Set ENABLE_SEQ2SEQ=1 to enable.")

        self.model_name = model_name or MODEL_NAME_DEFAULT
        self.device = device
        self._loaded = False
        self._tokenizer = None
        self._model = None

    def _lazy_load(self):
        if self._loaded:
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        except Exception as e:
            raise RuntimeError(f"transformers library not available: {e}")

        try:
            print(f"[Seq2Seq] Loading model: {self.model_name} ...")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

            # Device handling
            try:
                import torch
                if self.device is None:
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model.to(self.device)
                print(f"[Seq2Seq] Loaded on device: {self.device}")
            except Exception:
                print("[Seq2Seq] Failed to set device, using CPU fallback")

            self._loaded = True
        except Exception as e:
            raise RuntimeError(f"failed to load seq2seq model '{self.model_name}': {e}")

    def generate_reply(self, query: str, context: Optional[str] = None, max_length: int = 128) -> str:
        self._lazy_load()

        if not self._loaded or self._model is None:
            raise RuntimeError("seq2seq model not loaded")

        input_text = query
        if context:
            input_text = f"Context: {context}\nUser: {query}\nAssistant:"

        # Encode
        inputs = self._tokenizer(input_text, return_tensors="pt", truncation=True)

        # Move to device
        try:
            import torch
            if self.device and self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
        except Exception:
            pass

        # Generate
        gen = self._model.generate(
            **inputs,
            max_length=max_length,
            num_beams=4,
            early_stopping=True
        )

        return self._tokenizer.decode(gen[0], skip_special_tokens=True)


# Singleton untuk dipakai di API
_GEN_INSTANCE: Optional[Seq2SeqGenerator] = None


def get_generator():
    global _GEN_INSTANCE
    if _GEN_INSTANCE is None:
        try:
            _GEN_INSTANCE = Seq2SeqGenerator()
        except Exception:
            _GEN_INSTANCE = None
    return _GEN_INSTANCE


def generate_reply_safe(query: str, context: Optional[str] = None, max_length: int = 128) -> str:
    gen = get_generator()
    if not gen:
        raise RuntimeError("seq2seq generator not available or disabled")
    return gen.generate_reply(query, context=context, max_length=max_length)


# =============================
# TEST MODE (kalau dijalankan langsung)
# =============================
if __name__ == "__main__":
    print("=== Seq2Seq Self Test ===")
    print(f"ENABLE_SEQ2SEQ = {ENABLED}")
    print(f"MODEL = {MODEL_NAME_DEFAULT}")

    if not ENABLED:
        print("❌ Seq2Seq tidak aktif. Jalankan dulu:")
        print('   PowerShell:   $env:ENABLE_SEQ2SEQ="1"')
        print('   CMD:          set ENABLE_SEQ2SEQ=1')
        quit()

    try:
        reply = generate_reply_safe(
            "Aku mau tanya soal persiapan pernikahan, mulai dari mana?",
            context="User ingin konsultasi wedding planning"
        )
        print("\nGenerated Reply:")
        print(reply)
    except Exception as e:
        print("\n❌ ERROR:")
        print(e)
