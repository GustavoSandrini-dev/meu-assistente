#!/usr/bin/env python3
# Gera precos-alimentos.json e preparacoes.json a partir da TACO.
# rend = kg comprado por kg servido (perda de cocção / rendimento).
import json, unicodedata, sys

TACO = {a["i"]: a for a in json.load(open("alimentos-taco.json"))}

# Leite líquido está com "*" (sem valor) nesta base da TACO. Complementado
# com os valores da 4ª edição impressa; kcal calculada por Atwater (4/4/9).
COMPL = [
  dict(i=458, n="Leite, de vaca, integral", c="Leite e derivados", p=3.2, b=4.7, g=3.3, f=0.0, s=63.8, ca=122.6, fe=0.04, vc=0.9, sa=1.9, co=10.0, est=1),
  dict(i=457, n="Leite, de vaca, desnatado, UHT", c="Leite e derivados", p=3.4, b=4.9, g=0.2, f=0.0, s=51.1, ca=133.8, fe=0.04, vc=0.9, sa=0.1, co=2.0, est=1),
]
for x in COMPL:
    x["k"] = round(x["p"] * 4 + x["b"] * 4 + x["g"] * 9, 2)
    TACO[x["i"]] = x

# ---------------------------------------------------------------- ingredientes
# slug: (taco_id, nome curto, R$/kg (ou R$/L), rend, medida, [alergenos])
ING = {
 # --- carboidratos
 "arroz_branco":      (3,   "Arroz branco cozido",        7.50, .35, "cozido", []),
 "arroz_integral":    (1,   "Arroz integral cozido",     11.00, .35, "cozido", []),
 "macarrao":          (40,  "Macarrão",                   8.50, 1.0, "cru",    ["gluten"]),
 "pao_frances":       (53,  "Pão francês",               16.00, 1.0, "un",     ["gluten"]),
 "pao_integral":      (52,  "Pão de forma integral",     22.00, 1.0, "fatia",  ["gluten"]),
 "aveia":             (7,   "Aveia em flocos",           16.00, 1.0, "cru",    ["gluten"]),
 "tapioca":           (146, "Goma de tapioca",           12.00, 1.0, "cru",    []),
 "batata":            (91,  "Batata cozida",              6.00, 1.2, "cozido", []),
 "batata_doce":       (88,  "Batata-doce cozida",         7.00, 1.2, "cozido", []),
 "mandioca":          (129, "Mandioca cozida",            7.00, 1.3, "cozido", []),
 "farinha_mandioca":  (121, "Farinha de mandioca",        9.00, 1.0, "cru",    []),
 "polenta":           (62,  "Polenta",                    7.00, 1.0, "pronta", []),
 "farinha_milho":     (33,  "Farinha de milho (cuscuz)",  7.00, 1.0, "cru",    []),
 "milho_verde":       (45,  "Milho verde",               12.00, 1.0, "escor.", []),
 "pao_queijo":        (140, "Pão de queijo",             30.00, 1.0, "un",     ["lactose"]),
 "torrada":           (63,  "Torrada",                   25.00, 1.0, "fatia",  ["gluten"]),
 "cream_cracker":     (13,  "Biscoito cream cracker",    18.00, 1.0, "un",     ["gluten"]),
 # --- proteínas animais
 "frango_peito":      (410, "Peito de frango grelhado",  24.00, 1.30, "grelh.", ["frango"]),
 "frango_coxa":       (396, "Coxa de frango assada",     14.00, 1.25, "assada", ["frango"]),
 "frango_sobrecoxa":  (413, "Sobrecoxa sem pele assada", 16.00, 1.25, "assada", ["frango"]),
 "frango_desfiado":   (408, "Frango cozido desfiado",    20.00, 1.30, "cozido", ["frango"]),
 "peru":              (425, "Peito de peru assado",      45.00, 1.25, "assado", ["frango"]),
 "linguica_frango":   (420, "Linguiça de frango",        26.00, 1.15, "grelh.", ["frango"]),
 "patinho":           (377, "Patinho grelhado",          46.00, 1.30, "grelh.", ["boi"]),
 "acem_moido":        (326, "Carne moída (acém)",        38.00, 1.35, "cozida", ["boi"]),
 "musculo":           (371, "Músculo cozido",            36.00, 1.40, "cozido", ["boi"]),
 "coxao_mole":        (351, "Coxão mole cozido",         48.00, 1.30, "cozido", ["boi"]),
 "contra_file":       (346, "Contrafilé grelhado",       56.00, 1.30, "grelh.", ["boi"]),
 "figado":            (356, "Fígado bovino grelhado",    24.00, 1.30, "grelh.", ["boi"]),
 "porco_lombo":       (432, "Lombo suíno assado",        32.00, 1.30, "assado", ["porco"]),
 "porco_bisteca":     (429, "Bisteca suína grelhada",    28.00, 1.30, "grelh.", ["porco"]),
 "presunto":          (439, "Presunto magro",            40.00, 1.0,  "fatia",  ["porco"]),
 "ovo_cozido":        (488, "Ovo cozido",                14.00, 1.0,  "un",     ["ovo"]),
 "ovo_frito":         (490, "Ovo frito",                 14.00, 1.0,  "un",     ["ovo"]),
 "merluza":           (301, "Filé de merluza assado",    32.00, 1.25, "assado", ["peixe"]),
 "pintado":           (313, "Pintado grelhado",          38.00, 1.25, "grelh.", ["peixe"]),
 "atum_lata":         (277, "Atum em conserva",          55.00, 1.0,  "escor.", ["peixe"]),
 "sardinha_lata":     (319, "Sardinha em conserva",      40.00, 1.0,  "escor.", ["peixe"]),
 "salmao":            (317, "Salmão grelhado",           95.00, 1.25, "grelh.", ["peixe"]),
 "camarao":           (284, "Camarão cozido",            80.00, 1.30, "cozido", ["frutos_mar"]),
 # --- laticínios
 "leite":             (458, "Leite integral",             5.50, 1.0, "ml",   ["lactose"]),
 "leite_desnatado":   (457, "Leite desnatado",            6.00, 1.0, "ml",   ["lactose"]),
 "iogurte":           (448, "Iogurte natural",           14.00, 1.0, "pote", ["lactose"]),
 "queijo_minas":      (461, "Queijo minas frescal",      45.00, 1.0, "fatia",["lactose"]),
 "mussarela":         (463, "Queijo mussarela",          48.00, 1.0, "fatia",["lactose"]),
 "ricota":            (469, "Ricota",                    32.00, 1.0, "-",    ["lactose"]),
 "requeijao":         (465, "Queijo cremoso",            40.00, 1.0, "-",    ["lactose"]),
 "parmesao":          (464, "Parmesão ralado",           85.00, 1.0, "-",    ["lactose"]),
 "creme_leite":       (447, "Creme de leite",            25.00, 1.0, "-",    ["lactose"]),
 # --- leguminosas e vegetais proteicos
 "feijao_carioca":    (561, "Feijão carioca cozido",      9.00, .42, "cozido", []),
 "feijao_preto":      (567, "Feijão preto cozido",        9.00, .42, "cozido", []),
 "lentilha":          (577, "Lentilha cozida",           14.00, .42, "cozida", []),
 "grao_de_bico":      (575, "Grão-de-bico",              16.00, .42, "cru",    []),
 "tofu":              (584, "Tofu",                      30.00, 1.0, "-",      ["soja"]),
 "leite_soja":        (582, "Bebida de soja",            12.00, 1.0, "ml",     ["soja"]),
 "ervilha":           (560, "Ervilha em conserva",       14.00, 1.0, "escor.", []),
 # --- hortaliças
 "alface":            (78,  "Alface",                    12.00, 1.0, "cru", []),
 "rucula":            (152, "Rúcula",                    25.00, 1.0, "cru", []),
 "tomate":            (157, "Tomate",                     9.00, 1.0, "cru", []),
 "cenoura_crua":      (110, "Cenoura ralada",             6.00, 1.0, "cru", []),
 "cenoura":           (109, "Cenoura cozida",             6.00, 1.15,"cozida", []),
 "brocolis":          (100, "Brócolis cozido",           16.00, 1.20,"cozido", []),
 "couve":             (116, "Couve refogada",            12.00, 1.15,"refog.", []),
 "abobrinha":         (72,  "Abobrinha refogada",         8.00, 1.15,"refog.", []),
 "beterraba":         (97,  "Beterraba cozida",           7.00, 1.15,"cozida", []),
 "chuchu":            (112, "Chuchu cozido",              5.00, 1.15,"cozido", []),
 "repolho":           (149, "Repolho",                    5.00, 1.0, "cru", []),
 "pepino":            (142, "Pepino",                     7.00, 1.0, "cru", []),
 "espinafre":         (120, "Espinafre refogado",        20.00, 1.20,"refog.", []),
 "vagem":             (162, "Vagem",                     14.00, 1.15,"cozida", []),
 "abobora":           (64,  "Abóbora cabotiá cozida",     7.00, 1.15,"cozida", []),
 "berinjela":         (95,  "Berinjela cozida",          10.00, 1.15,"cozida", []),
 "couve_flor":        (118, "Couve-flor cozida",         14.00, 1.20,"cozida", []),
 "quiabo":            (147, "Quiabo",                    14.00, 1.15,"refog.", []),
 "cebola":            (107, "Cebola",                     6.00, 1.0, "cru", []),
 "alho":              (82,  "Alho",                      30.00, 1.0, "cru", []),
 "pimentao":          (144, "Pimentão",                  10.00, 1.0, "cru", []),
 "molho_tomate":      (159, "Molho de tomate",           12.00, 1.0, "-",   []),
 "extrato_tomate":    (158, "Extrato de tomate",         20.00, 1.0, "-",   []),
 "palmito":           (138, "Palmito em conserva",       60.00, 1.0, "escor.", []),
 # --- frutas
 "banana":            (182, "Banana prata",               7.00, 1.0, "un", []),
 "maca":              (221, "Maçã",                      12.00, 1.0, "un", []),
 "mamao":             (226, "Mamão papaia",               7.00, 1.0, "-",  []),
 "laranja":           (214, "Laranja",                    5.00, 1.0, "un", []),
 "melancia":          (235, "Melancia",                   4.00, 1.0, "-",  []),
 "abacaxi":           (164, "Abacaxi",                    6.00, 1.0, "-",  []),
 "manga":             (231, "Manga",                      8.00, 1.0, "-",  []),
 "morango":           (239, "Morango",                   30.00, 1.0, "-",  []),
 "uva":               (256, "Uva",                       18.00, 1.0, "-",  []),
 "abacate":           (163, "Abacate",                   10.00, 1.0, "-",  []),
 "goiaba":            (200, "Goiaba",                     9.00, 1.0, "un", []),
 "melao":             (236, "Melão",                      7.00, 1.0, "-",  []),
 "tangerina":         (251, "Tangerina",                  7.00, 1.0, "un", []),
 "suco_laranja":      (215, "Suco de laranja",            8.00, 1.0, "ml", []),
 # --- gorduras, oleaginosas e extras
 "azeite":            (260, "Azeite de oliva",           45.00, 1.0, "ml", []),
 "oleo":              (272, "Óleo de soja",              10.00, 1.0, "ml", []),
 "manteiga":          (261, "Manteiga",                  55.00, 1.0, "-",  ["lactose"]),
 "margarina":         (263, "Margarina",                 22.00, 1.0, "-",  []),
 "castanha_caju":     (588, "Castanha de caju",          70.00, 1.0, "-",  ["oleaginosas"]),
 "castanha_para":     (589, "Castanha-do-pará",          90.00, 1.0, "-",  ["oleaginosas"]),
 "amendoim":          (558, "Amendoim torrado",          25.00, 1.0, "-",  ["amendoim"]),
 "amendoa":           (587, "Amêndoa",                   90.00, 1.0, "-",  ["oleaginosas"]),
 "coco":              (590, "Coco ralado",               12.00, 1.0, "-",  []),
 "linhaca":           (594, "Linhaça",                   25.00, 1.0, "-",  []),
 "gergelim":          (593, "Gergelim",                  40.00, 1.0, "-",  []),
 "cacau":             (183, "Cacau em pó",               60.00, 1.0, "-",  []),
 "farofa":            (131, "Farofa temperada",          18.00, 1.0, "-",  []),
}

# ------- ampliação (dados_extra.py) -------
try:
    from dados_extra import EXTRA_ING, EXTRA_P
    ING.update(EXTRA_ING)
except ImportError:
    EXTRA_P = []
try:
    from dados_lanches import LANCHES, PORT_SECO
except ImportError:
    LANCHES, PORT_SECO = [], set()

PROTEINA = {  # de qual proteína a preparação "é"
 "frango": ["frango_peito","frango_coxa","frango_sobrecoxa","frango_desfiado","linguica_frango","peru",
            "frango_caipira","frango_assado","coracao_frango","frango_milanesa","estrog_frango","salpicao","frango_acafrao"],
 "boi":    ["patinho","acem_moido","musculo","coxao_mole","contra_file","figado","alcatra","maminha",
            "lagarto","coxao_duro","cupim","file_mignon","carne_seca","hamburguer","quibe",
            "estrog_carne","arroz_carreteiro","bolonhesa","charuto_repolho","vaca_atolada","barreado"],
 "porco":  ["porco_lombo","porco_bisteca","presunto","pernil","feijoada","feijao_tropeiro","virado_paulista","manicoba"],
 "peixe":  ["merluza","pintado","atum_lata","sardinha_lata","salmao","camarao","abadejo","cacao",
            "corvina","bacalhau","sardinha_fresca","vatapa"],
 "ovo":    ["ovo_cozido","ovo_frito","ovo_codorna","clara"],
 "vegetal":["feijao_carioca","feijao_preto","lentilha","grao_de_bico","tofu","leite_soja",
            "feijao_fradinho","feijao_roxo","tremoco","baiao_dois"],
 "laticinio":["queijo_minas","mussarela","ricota","iogurte","leite","leite_desnatado","requeijao"],
}
DE_ING = {}
for p, lst in PROTEINA.items():
    for s in lst: DE_ING.setdefault(s, p)

# ------------------------------------------------------------- preparações
# (id, nome, [tipos], [(slug, gramas)], preparo curto, minutos)
P = [
# ---------------------------------------------------------------- CAFÉ
("cafe_pao_ovo","Pão francês com ovo mexido e café",["cafe"],
 [("pao_frances",50),("ovo_frito",50),("leite",150)],
 "Ovos mexidos em fogo baixo com um fio de óleo; pão francês e café com leite.",10),
("cafe_tapioca_queijo","Tapioca com queijo minas",["cafe"],
 [("tapioca",40),("queijo_minas",40),("laranja",130)],
 "Espalhe a goma na frigideira quente, recheie com o queijo e dobre.",8),
("cafe_aveia_banana","Mingau de aveia com banana",["cafe","ceia"],
 [("aveia",40),("leite",200),("banana",90)],
 "Aveia no leite em fogo baixo até engrossar; banana em rodelas por cima.",8),
("cafe_iogurte_granola","Iogurte com aveia, banana e castanha",["cafe","lanche"],
 [("iogurte",170),("aveia",30),("banana",90),("castanha_caju",15)],
 "Monte em camadas no pote. Dá para deixar pronto na véspera.",5),
("cafe_pao_integral_requeijao","Pão integral com queijo cremoso e mamão",["cafe"],
 [("pao_integral",50),("requeijao",30),("mamao",150)],
 "Torre as fatias, passe o queijo cremoso e sirva com a fruta.",5),
("cafe_cuscuz_ovo","Cuscuz nordestino com ovo",["cafe"],
 [("farinha_milho",60),("ovo_cozido",50),("leite",150)],
 "Hidrate a farinha com água e sal, cozinhe na cuscuzeira 8 min.",15),
("cafe_ovos_abacate","Ovos cozidos com abacate e torrada",["cafe"],
 [("ovo_cozido",100),("abacate",60),("torrada",30)],
 "Amasse o abacate com limão e sal, sirva sobre a torrada com os ovos.",10),
("cafe_vitamina","Vitamina de banana, aveia e leite",["cafe","lanche"],
 [("leite",250),("banana",90),("aveia",30),("linhaca",10)],
 "Bata tudo no liquidificador. Fica melhor com a banana congelada.",5),
("cafe_pao_queijo_fruta","Pão de queijo com café e fruta",["cafe"],
 [("pao_queijo",80),("leite",150),("maca",130)],
 "Assados na hora ou de forno; acompanhe com a fruta picada.",20),
("cafe_omelete_legumes","Omelete de tomate e cebola",["cafe","jantar"],
 [("ovo_frito",100),("tomate",50),("cebola",25),("pao_frances",50)],
 "Bata os ovos, junte o tomate e a cebola picados, doure dos dois lados.",12),
("cafe_mamao_aveia","Mamão com aveia e mel de castanha",["cafe","ceia"],
 [("mamao",200),("aveia",30),("castanha_para",15)],
 "Mamão picado com a aveia e as castanhas quebradas por cima.",4),
("cafe_leite_soja_frutas","Bebida de soja com frutas e granola",["cafe","lanche"],
 [("leite_soja",250),("morango",80),("aveia",30),("banana",60)],
 "Bata a bebida de soja com as frutas e finalize com a aveia.",5),
("cafe_ovo_batata_doce","Ovos com batata-doce",["cafe","lanche"],
 [("ovo_cozido",100),("batata_doce",120),("laranja",130)],
 "Batata-doce cozida e amassada, ovos cozidos em 10 min.",20),
("cafe_pao_atum","Pão integral com pasta de atum",["cafe","lanche"],
 [("pao_integral",50),("atum_lata",60),("tomate",40)],
 "Misture o atum escorrido com um pouco de queijo cremoso e tempere.",6),
# ---------------------------------------------------------------- LANCHE
("lanche_fruta_castanha","Fruta com castanhas",["lanche","ceia"],
 [("maca",130),("castanha_caju",25)],"Simples: fruta e um punhado de castanhas.",2),
("lanche_iogurte_fruta","Iogurte natural com fruta",["lanche","ceia"],
 [("iogurte",170),("morango",100)],"Amasse parte da fruta no iogurte para adoçar sem açúcar.",3),
("lanche_sanduiche_peru","Sanduíche de peito de peru e queijo",["lanche"],
 [("pao_integral",50),("peru",40),("mussarela",30),("alface",20)],
 "Monte o sanduíche e prense por 3 min na frigideira.",8),
("lanche_banana_amendoim","Banana com pasta de amendoim",["lanche","ceia"],
 [("banana",90),("amendoim",25)],"Banana cortada ao meio com o amendoim triturado.",3),
("lanche_ovo_fruta","Ovos cozidos com fruta",["lanche"],
 [("ovo_cozido",100),("tangerina",130)],"Deixe os ovos cozidos prontos na geladeira para a semana.",12),
("lanche_vitamina_abacate","Creme de abacate com cacau",["lanche","ceia"],
 [("abacate",100),("cacau",8),("leite",120)],"Bata tudo até virar um creme. Gelado fica melhor.",5),
("lanche_queijo_torrada","Torradas com queijo minas e tomate",["lanche"],
 [("torrada",30),("queijo_minas",50),("tomate",50)],"Torrada, queijo em fatias e tomate com azeite.",5),
("lanche_mix_frutas","Salada de frutas",["lanche","ceia"],
 [("mamao",120),("banana",60),("abacaxi",80),("laranja",100)],"Pique tudo e regue com o suco da laranja.",8),
("lanche_grao_de_bico","Grão-de-bico assado temperado",["lanche"],
 [("grao_de_bico",60),("azeite",5)],"Cozido, seco no pano e assado a 200 °C por 25 min com páprica.",30),
("lanche_pao_queijo_cafe","Pão de queijo",["lanche"],
 [("pao_queijo",80),("suco_laranja",200)],"Do congelador direto pro forno.",20),
("lanche_melancia_castanha","Melancia com castanha-do-pará",["lanche","ceia"],
 [("melancia",250),("castanha_para",15)],"Refrescante e barato na safra.",3),
("lanche_ricota_torrada","Pasta de ricota com torrada",["lanche"],
 [("ricota",70),("torrada",30),("cenoura_crua",40)],
 "Amasse a ricota com azeite, sal e cheiro-verde; use a cenoura em palitos.",6),
("lanche_uva_queijo","Uva com queijo minas",["lanche","ceia"],
 [("uva",120),("queijo_minas",40)],"Combinação simples de fruta e proteína.",2),
("lanche_smoothie_manga","Smoothie de manga com iogurte",["lanche"],
 [("iogurte",150),("manga",150)],"Bata a manga congelada com o iogurte.",4),
# ---------------------------------------------------------------- ALMOÇO
("almoco_frango_arroz_feijao","Frango grelhado, arroz, feijão e salada",["almoco","jantar"],
 [("frango_peito",130),("arroz_branco",150),("feijao_carioca",130),("alface",40),("tomate",50),("azeite",5)],
 "Tempere o frango com alho, limão e sal 30 min antes; grelhe 6 min de cada lado.",35),
("almoco_carne_moida_abobrinha","Carne moída com abobrinha, arroz e feijão",["almoco","jantar"],
 [("acem_moido",120),("abobrinha",100),("arroz_branco",150),("feijao_carioca",130)],
 "Refogue a carne com cebola e alho, junte a abobrinha em cubos no fim.",35),
("almoco_peixe_batata","Merluza assada com batata e brócolis",["almoco","jantar"],
 [("merluza",150),("batata",150),("brocolis",100),("azeite",8)],
 "Peixe no forno a 200 °C por 20 min com limão; batata e brócolis no vapor.",35),
("almoco_feijoada_light","Feijão preto com lombo, arroz e couve",["almoco"],
 [("feijao_preto",150),("porco_lombo",90),("arroz_branco",150),("couve",60),("laranja",100)],
 "Cozinhe o feijão com o lombo em cubos; couve refogada no alho.",50),
("almoco_frango_batata_doce","Frango desfiado com batata-doce e salada",["almoco","jantar"],
 [("frango_desfiado",130),("batata_doce",180),("repolho",60),("cenoura_crua",40),("azeite",6)],
 "Frango cozido e desfiado no molho de tomate; salada de repolho com cenoura.",35),
("almoco_macarrao_carne","Macarrão ao sugo com carne moída",["almoco","jantar"],
 [("macarrao",90),("acem_moido",110),("molho_tomate",100),("parmesao",10),("alface",40)],
 "Molho refogado com a carne por 20 min; macarrão al dente.",30),
("almoco_lentilha_arroz","Arroz com lentilha, ovo e legumes",["almoco","jantar"],
 [("lentilha",150),("arroz_integral",150),("ovo_cozido",50),("cenoura",80),("azeite",6)],
 "Lentilha cozida com louro; sirva com o ovo cortado ao meio.",35),
("almoco_bife_purê","Patinho grelhado com purê e vagem",["almoco","jantar"],
 [("patinho",130),("batata",150),("leite",40),("vagem",100)],
 "Purê com a batata cozida, leite e um fio de azeite; bife selado.",35),
("almoco_frango_quiabo","Frango com quiabo, polenta e salada",["almoco"],
 [("frango_coxa",140),("quiabo",100),("polenta",150),("tomate",50)],
 "Refogue o quiabo separado para não babar; junte ao frango no fim.",45),
("almoco_peixe_pintado","Pintado grelhado com arroz e legumes",["almoco","jantar"],
 [("pintado",150),("arroz_branco",150),("abobora",120),("couve",50)],
 "Peixe na chapa 5 min de cada lado; abóbora cozida no ponto de amassar.",35),
("almoco_grao_de_bico_legumes","Grão-de-bico com legumes e arroz integral",["almoco","jantar"],
 [("grao_de_bico",140),("arroz_integral",150),("cenoura",70),("abobrinha",80),("azeite",8)],
 "Deixe o grão de molho na véspera; refogue com cominho e páprica.",45),
("almoco_musculo_mandioca","Músculo cozido com mandioca",["almoco"],
 [("musculo",130),("mandioca",180),("cenoura",70),("couve",50)],
 "Panela de pressão 25 min com a carne, depois junte a mandioca.",50),
("almoco_atum_macarrao","Macarrão com atum e tomate",["almoco","jantar"],
 [("macarrao",90),("atum_lata",90),("tomate",80),("azeite",8),("rucula",30)],
 "Refogue o tomate no azeite, junte o atum escorrido e a massa.",25),
("almoco_omelete_recheado","Omelete recheado com salada e arroz",["almoco","jantar"],
 [("ovo_frito",120),("mussarela",30),("arroz_integral",120),("alface",40),("tomate",50)],
 "Três ovos batidos, recheio no meio e dobra.",20),
("almoco_frango_xadrez","Frango com pimentão e castanha, arroz",["almoco","jantar"],
 [("frango_peito",130),("pimentao",60),("cebola",40),("castanha_caju",20),("arroz_branco",150)],
 "Frango em cubos em fogo alto; junte os legumes por último para ficarem crocantes.",30),
("almoco_bisteca_farofa","Bisteca suína com farofa e salada",["almoco"],
 [("porco_bisteca",130),("farofa",40),("arroz_branco",130),("repolho",60)],
 "Bisteca temperada na véspera; farofa na manteiga com cebola.",30),
("almoco_figado_acebolado","Fígado acebolado com arroz e feijão",["almoco"],
 [("figado",120),("cebola",50),("arroz_branco",150),("feijao_carioca",130),("couve",50)],
 "Fígado fino, fogo alto e rápido, senão endurece.",30),
("almoco_camarao_arroz","Arroz com camarão e legumes",["almoco","jantar"],
 [("camarao",130),("arroz_branco",150),("pimentao",50),("tomate",60),("azeite",8)],
 "Camarão cozinha em 3 min; passar disso vira borracha.",30),
("almoco_salmao_legumes","Salmão grelhado com legumes",["almoco","jantar"],
 [("salmao",130),("batata_doce",150),("brocolis",100),("azeite",6)],
 "Salmão com a pele para baixo por 5 min, vira e desliga.",30),
("almoco_tofu_legumes","Tofu grelhado com arroz integral e legumes",["almoco","jantar"],
 [("tofu",150),("arroz_integral",150),("brocolis",100),("cenoura",60),("gergelim",8),("azeite",8)],
 "Prense o tofu, tempere com shoyu e alho, grelhe até dourar.",30),
("almoco_coxao_mole_salada","Coxão mole com salada completa e arroz",["almoco","jantar"],
 [("coxao_mole",130),("arroz_branco",150),("alface",40),("tomate",60),("pepino",50),("beterraba",60),("azeite",8)],
 "Carne em tiras selada; salada colorida com azeite e limão.",30),
("almoco_frango_couve_flor","Frango assado com couve-flor gratinada",["almoco","jantar"],
 [("frango_sobrecoxa",140),("couve_flor",150),("mussarela",30),("arroz_integral",120)],
 "Couve-flor cozida, coberta com o queijo e gratinada 10 min.",45),
# ---------------------------------------------------------------- JANTAR
("jantar_sopa_legumes","Sopa de legumes com frango",["jantar"],
 [("frango_desfiado",110),("batata",100),("cenoura",70),("abobrinha",70),("couve",40)],
 "Cozinhe tudo junto e amasse parte dos legumes para encorpar.",40),
("jantar_creme_abobora","Creme de abóbora com frango desfiado",["jantar"],
 [("abobora",250),("frango_desfiado",100),("leite",50),("azeite",6)],
 "Abóbora cozida e batida; frango desfiado por cima.",35),
("jantar_wrap_frango","Sanduíche quente de frango e salada",["jantar"],
 [("pao_integral",60),("frango_desfiado",100),("queijo_minas",30),("alface",30),("tomate",40)],
 "Frango desfiado temperado, monta e prensa.",15),
("jantar_sopa_feijao","Sopa de feijão com legumes e macarrão",["jantar"],
 [("feijao_carioca",160),("macarrao",40),("cenoura",60),("couve",40)],
 "Bata parte do feijão para engrossar o caldo.",35),
("jantar_ovos_legumes","Ovos mexidos com legumes salteados",["jantar"],
 [("ovo_frito",100),("abobrinha",90),("tomate",60),("pao_integral",50)],
 "Legumes em cubinhos no fogo alto, ovos por último.",20),
("jantar_peixe_purê","Merluza com purê de batata-doce",["jantar"],
 [("merluza",140),("batata_doce",160),("vagem",90),("azeite",6)],
 "Purê de batata-doce sem leite, só azeite e sal.",30),
("jantar_salada_atum","Salada completa com atum e grão-de-bico",["jantar"],
 [("atum_lata",90),("grao_de_bico",100),("alface",50),("tomate",60),("pepino",50),("azeite",10)],
 "Tudo frio, montado na hora, com limão e azeite.",15),
("jantar_frango_legumes_forno","Frango e legumes assados na assadeira",["jantar","almoco"],
 [("frango_sobrecoxa",140),("batata",130),("cenoura",80),("cebola",50),("azeite",10)],
 "Tudo na mesma assadeira a 200 °C por 40 min, mexendo na metade.",50),
("jantar_omelete_espinafre","Omelete de espinafre e ricota",["jantar"],
 [("ovo_frito",100),("espinafre",80),("ricota",50),("torrada",30)],
 "Refogue o espinafre, escorra bem e junte aos ovos.",18),
("jantar_sopa_lentilha","Sopa de lentilha com legumes",["jantar"],
 [("lentilha",160),("cenoura",70),("batata",90),("cebola",40),("azeite",8)],
 "Lentilha não precisa de molho; 25 min de panela resolve.",35),
("jantar_berinjela_recheada","Berinjela recheada com carne moída",["jantar","almoco"],
 [("berinjela",200),("acem_moido",110),("molho_tomate",80),("mussarela",30)],
 "Asse a berinjela, recheie com a carne e gratine.",45),
("jantar_panqueca_frango","Panqueca de frango com salada",["jantar"],
 [("macarrao",50),("frango_desfiado",110),("molho_tomate",80),("alface",40)],
 "Massa fina de trigo, leite e ovo; recheie e cubra com molho.",35),
("jantar_caldo_mandioca","Caldo de mandioca com carne desfiada",["jantar"],
 [("mandioca",200),("musculo",100),("cebola",40),("couve",40)],
 "Mandioca batida no caldo do cozimento da carne.",45),
("jantar_tofu_legumes","Tofu com legumes no shoyu",["jantar"],
 [("tofu",150),("brocolis",100),("cenoura",70),("gergelim",8),("azeite",8)],
 "Fogo alto e panela quente para não soltar água.",25),
("jantar_sardinha_salada","Sardinha com salada de batata",["jantar"],
 [("sardinha_lata",90),("batata",150),("cebola",40),("alface",40),("azeite",8)],
 "Batata cozida e temperada ainda morna absorve melhor.",25),
("jantar_polenta_frango","Polenta cremosa com frango ao molho",["jantar"],
 [("polenta",180),("frango_desfiado",110),("molho_tomate",90),("parmesao",10)],
 "Polenta mole, frango no molho por cima.",30),
("jantar_sopa_ervilha","Sopa de ervilha com legumes",["jantar"],
 [("ervilha",150),("batata",100),("cenoura",60),("cebola",40),("azeite",6)],
 "Bata metade para dar cremosidade.",30),
("jantar_salada_frango_grelhado","Salada morna de frango e legumes",["jantar"],
 [("frango_peito",130),("abobrinha",90),("tomate",60),("rucula",40),("azeite",10)],
 "Legumes grelhados na mesma frigideira do frango.",25),
# ---------------------------------------------------------------- CEIA
("ceia_iogurte","Iogurte natural",["ceia"],[("iogurte",170)],"Puro ou com canela.",1),
("ceia_leite_canela","Leite morno com canela",["ceia"],[("leite",200)],"Aquecer sem ferver.",4),
("ceia_fruta","Fruta da estação",["ceia"],[("banana",90)],"A mais barata da feira.",1),
("ceia_castanhas","Mix de castanhas",["ceia"],[("castanha_caju",20),("castanha_para",10)],"Um punhado só.",1),
("ceia_cha_torrada","Torrada com queijo cremoso",["ceia"],[("torrada",25),("requeijao",25)],"Leve para não pesar.",4),
("ceia_ricota_mel","Ricota com fruta",["ceia"],[("ricota",60),("maca",100)],"Ricota amassada com a fruta picada.",4),
("ceia_leite_soja","Bebida de soja com cacau",["ceia"],[("leite_soja",220),("cacau",6)],"Bata com gelo.",3),
("ceia_abacate","Abacate amassado com limão",["ceia"],[("abacate",90)],"Só o abacate, limão e uma pitada de sal.",3),
]

# --------------------------------------------------------------- construção
def nutri(itens):
    t = dict(kcal=0, prot=0, carb=0, gord=0, fibra=0, sodio=0, custo=0)
    for slug, g in itens:
        tid, nome, rs, rend, med, _al = ING[slug]
        a = TACO[tid]
        f = g / 100.0
        t["kcal"]  += (a.get("k") or 0) * f
        t["prot"]  += (a.get("p") or 0) * f
        t["carb"]  += (a.get("b") or 0) * f
        t["gord"]  += (a.get("g") or 0) * f
        t["fibra"] += (a.get("f") or 0) * f
        t["sodio"] += (a.get("s") or 0) * f
        t["custo"] += g * rend * rs / 1000.0
    return {k: round(v, 2) for k, v in t.items()}

precos = []
for slug, (tid, nome, rs, rend, med, al) in ING.items():
    a = TACO[tid]
    faixa = 1 if rs <= 15 else (2 if rs <= 45 else 3)
    precos.append(dict(slug=slug, nome=nome, taco=tid, taco_nome=a["n"],
                       rs_kg=rs, rend=rend, medida=med, faixa=faixa, cat=a["c"],
                       alerg=al, prot_tipo=DE_ING.get(slug),
                       # nutrição por 100 g, para o gerador escalar ingrediente a ingrediente
                       k=a.get("k") or 0, p=a.get("p") or 0, b=a.get("b") or 0,
                       g=a.get("g") or 0, f=a.get("f") or 0, s=a.get("s") or 0,
                       sa=a.get("sa") or 0, co=a.get("co") or 0, fe=a.get("fe") or 0,
                       veg=a["c"] in ("Verduras, hortaliças e derivados","Frutas e derivados")))
precos.sort(key=lambda x: x["slug"])

P = P + EXTRA_P + LANCHES
preps, erros = [], []
for pid, nome, tipos, itens, prep, tempo in P:
    for slug, _g in itens:
        if slug not in ING: erros.append(f"{pid}: ingrediente '{slug}' não existe")
    if erros: continue
    n = nutri(itens)
    al = sorted({a for s, _ in itens for a in ING[s][5]})
    prots = sorted({DE_ING[s] for s, _ in itens if s in DE_ING and DE_ING[s] != "laticinio"})
    animal = {"frango", "boi", "porco", "peixe", "frutos_mar"} & set(al) | \
             {a for a in al if a in ("frango", "boi", "porco", "peixe", "frutos_mar")}
    vegetariano = not animal
    vegano = vegetariano and "lactose" not in al and "ovo" not in al
    custo = n.pop("custo")
    port = pid.startswith("lv_")
    preps.append(dict(id=pid, nome=nome, tipos=tipos,
                      port=port, port_seco=pid in PORT_SECO,
                      itens=[dict(slug=s, g=g) for s, g in itens],
                      preparo=prep, tempo=tempo, alerg=al, prot_tipos=prots,
                      vegetariano=vegetariano, vegano=vegano,
                      custo=round(custo, 2),
                      faixa=1 if custo <= 6 else (2 if custo <= 12 else 3),
                      **n))

if erros:
    print("ERROS:", *erros, sep="\n "); sys.exit(1)

meta = dict(versao=1, data_ref="2026-08",
            fonte_nutri="TACO 4ª ed. (UNICAMP)",
            fonte_precos="estimativa de mercado — ajuste na tela de preços")
json.dump(dict(**meta, itens=precos), open("precos-alimentos.json", "w"),
          ensure_ascii=False, separators=(",", ":"))
json.dump(dict(**meta, itens=preps), open("preparacoes.json", "w"),
          ensure_ascii=False, separators=(",", ":"))

# adiciona o leite complementado à TACO do app
taco_out = list(json.load(open("alimentos-taco.json")))
ids = {a["i"] for a in taco_out}
for x in COMPL:
    if x["i"] not in ids: taco_out.append(x)
taco_out.sort(key=lambda a: a["i"])
json.dump(taco_out, open("alimentos-taco.json", "w"), ensure_ascii=False, separators=(",", ":"))

print(f"ingredientes: {len(precos)}   preparações: {len(preps)}   alimentos TACO: {len(taco_out)}")
por = {}
for p in preps:
    for t in p["tipos"]: por[t] = por.get(t, 0) + 1
print("por tipo:", por)
print("kcal min/max:", min(p['kcal'] for p in preps), max(p['kcal'] for p in preps))
print("custo min/max: R$", min(p['custo'] for p in preps), max(p['custo'] for p in preps))
print("vegetarianas:", sum(1 for p in preps if p['vegetariano']), " veganas:", sum(1 for p in preps if p['vegano']))
