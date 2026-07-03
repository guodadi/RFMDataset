"""Backward-compatible import path for the RFMDataset LLM client."""

from rfmdataset.llm import GPTChatter, GPT_Chatter, MissingCredentialError

__all__ = ["GPTChatter", "GPT_Chatter", "MissingCredentialError"]
