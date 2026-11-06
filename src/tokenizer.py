"""Tokenización sin ejecutar texto ingresado por el usuario."""

import re
from dataclasses import dataclass

from errores import ErrorLexico


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str
    posicion: int


class Tokenizer:
    SIMBOLOS = {"¬": "NO", "~": "NO", "!": "NO", "∧": "Y", "&": "Y",
                "∨": "O", "|": "O", "→": "IMPLICA", "∀": "TODOS",
                "∃": "EXISTE", "(": "ABRE", ")": "CIERRA", ",": "COMA", ".": "PUNTO"}

    def tokenizar(self, texto):
        if not isinstance(texto, str):
            raise ErrorLexico("La fórmula debe ser texto.")
        tokens, i = [], 0
        while i < len(texto):
            if texto[i].isspace():
                i += 1
                continue
            if texto.startswith("->", i):
                tokens.append(Token("IMPLICA", "->", i))
                i += 2
                continue
            if texto[i] in self.SIMBOLOS:
                tokens.append(Token(self.SIMBOLOS[texto[i]], texto[i], i))
                i += 1
                continue
            nombre = re.match(r"[A-Za-z_][A-Za-z_0-9]*", texto[i:])
            if nombre:
                valor = nombre.group()
                tipo = {"forall": "TODOS", "exists": "EXISTE"}.get(valor, "ID")
                tokens.append(Token(tipo, valor, i))
                i += len(valor)
                continue
            raise ErrorLexico(f"Carácter no permitido: {texto[i]!r}.", posicion=i, texto=texto)
        tokens.append(Token("FIN", "", len(texto)))
        return tokens


def tokenizar(texto):
    return Tokenizer().tokenizar(texto)
