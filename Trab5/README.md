# Tiles automáticos

Demonstração em Pygame do método **desacoplado + bordas**, apresentado na aula 10.
As células de pedra têm colisão; as células de grama permitem a passagem. As
bordas são posicionadas automaticamente sempre que dois tipos diferentes se
encontram. Cada célula é desenhada como uma sprite procedural simples, com
pequenas variações para facilitar a leitura do mapa.

O código separa as responsabilidades nas classes `Tile`, `TileMap`, `Player`,
`HUD` e `Game`: cada uma cuida, respectivamente, da célula, do mapa, do
personagem, da interface e do ciclo principal.

Os módulos também estão separados: `tile.py`, `tile_map.py`, `player.py`,
`hud.py` e `game.py`. As dimensões e cores compartilhadas ficam em `config.py`;
`main.py` inicia o jogo.

## Executar

```powershell
python -m pip install pygame
python main.py
```

## Controles

- Clique esquerdo no mapa: pinta com o tipo selecionado.
- Clique direito no mapa: transforma a célula em grama sem colisão.
- `1` ou `2`: seleciona pedra com colisão ou grama sem colisão.
- `M`: alterna o pincel.
- `WASD` ou setas: move o personagem; pedras bloqueiam o movimento.
- `R`: gera um mapa aleatório.
- `C`: limpa as células sólidas.
- `Esc`: fecha a janela.
