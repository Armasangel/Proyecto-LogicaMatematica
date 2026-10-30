from controlador import Controlador
from interfaz import VentanaPrincipal


def main():
    controlador = Controlador()
    app = VentanaPrincipal(controlador)
    app.mainloop()


if __name__ == "__main__":
    main()