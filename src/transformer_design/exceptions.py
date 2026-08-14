"""Transformatör tasarımı özel hataları."""

class TransformerDesignError(Exception):
    """Genel tasarım hatası."""

class UnsupportedConnectionGroupError(TransformerDesignError):
    """Desteklenmeyen veya hatalı bağlantı grubu hatası."""

class MissingDataError(TransformerDesignError):
    """Eksik veri hatası."""

class PhysicallyInconsistentDataError(TransformerDesignError):
    """Fiziksel olarak tutarsız veya geçersiz veri hatası."""
