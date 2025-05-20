class CategoryManager:
    """
    Gestión estática de categorías e ítems en memoria.

    Define tus categorías y sus ítems IDs directamente en la clase.
    Solo provee métodos para consultar.
    """
    # Definición estática de categorías e ítems
    CATEGORIES: dict[str, list[str]] = {
        "corazones": [
            "[T1]FACTION_SWAMP_TOKEN_1","[T1]FACTION_MOUNTAIN_TOKEN_1","[T1]FACTION_STEPPE_TOKEN_1",
            "[T1]FACTION_CAERLEON_TOKEN_1","[T1]FACTION_HIGHLAND_TOKEN_1","[T1]FACTION_FOREST_TOKEN_1",
            "[T1]FACTION_SWAMP_TOKEN_1"
        ],
        "animales_granja": [
            "[T3-T8]FARM_OX_BABY","[T3-T8]FARM_OX_GROWN","[T3-T8]FARM_HORSE_BABY","[T3-T8]FARM_HORSE_GROWN",
            "[T6-T8]FARM_DIREWOLF_BABY","[T7]FARM_DIREBOAR_BABY","[T8]FARM_DIREBEAR_BABY","[T7]FARM_SWAMPDRAGON_BABY",
            "[T8]FARM_MAMMOTH_BABY","[T5]FARM_COUGAR_BABY","[T4-T6]FARM_GIANTSTAG_BABY","[T6]FARM_GIANTSTAG_MOOSE_BABY"
        ],
        "semillas": [
            "[T6-T8]FARM_CORN_SEED","[T6-T8]FARM_POTATO_SEED","[T6-T8]FARM_PUMPKIN_SEED",
            "[T6-T8]FARM_MULLEIN_SEED","[T6-T8]FARM_CABBAGE_SEED","[T6-T8]FARM_YARROW_SEED"
        ],
        "tomos": [
            "[T4]SKILLBOOK_STANDARD", "[T4-T8]SKILLBOOK_GATHER_ROCK","[T4-T8]SKILLBOOK_GATHER_HIDE"
        ],
        "artefactos": [
            "[T4-T8]ARTEFACT_2H_CURSEDSTAFF_MORGANA"
        ],
        "monturas": [
            "MOUNT_OX","[T7]MOUNT_DIREBOAR","[T5]MOUNT_DIREBOAR_FW_LYMHURST","[T8]MOUNT_DIREBOAR_FW_LYMHURST_ELITE"
            "[T5]MOUNT_MOABIRD_FW_BRIDGEWATCH","[T5]MOUNT_RAM_FW_MARTLOCK","[T8]MOUNT_MAMMOTH_TRANSPORT", "[T2]MOUNT_MULE", "MOUNT_HORSE",
            "MOUNT_ARMORED_HORSE", "[T4]MOUNT_GIANTSTAG","[T5]MOUNT_OWL_FW_BRECILIEN","[T8]MOUNT_OWL_FW_BRECILIEN_ELITE"
            "[T6]MOUNT_GIANTSTAG_MOOSE", "MOUNT_SWAMPDRAGON",
            "MOUNT_SWAMPDRAGON_FW_THETFORD","MOUNT_GREYWOLF_FW_CAERLEON","[T6]MOUNT_DIREWOLF",
            "MOUNT_COUGAR_KEEPER","MOUNT_DIREBEAR","MOUNT_DIREBEAR_FW_FORTSTERLING","*UNIQUE_MOUNT_BATTLESPIDER_GOLD",
            "*UNIQUE_MOUNT_BASTION_CRYSTAL",
            "*UNIQUE_MOUNT_JUGGERNAUT_GOLD","*UNIQUE_MOUNT_TANKBEETLE_SILVER"
        ],
        "capas": [
            "[T4-T8]CAPE","[T4-T8]CAPEITEM_FW_LYMHURST","[T4-T8]CAPEITEM_FW_FORTSTERLING","[T4-T8]CAPEITEM_FW_THETFORD"
         ],
        
        "recursos": [
            "WOOD","ROCK","HIDE","FIBER","ORE","METALBAR","LEATHER","CLOTH","PLANKS","STONEBLOCK"
         ],
        
        "mago_obrero": [
            #PIROMANTE
            "[T4-T8]MAIN_FIRESTAFF","[T4-T8]2H_FIRESTAFF","[T4-T8]2H_INFERNOSTAFF","[T4-T8]MAIN_FIRESTAFF_KEEPER",
            "[T4-T8]2H_FIRESTAFF_HELL","[T4-T8]2H_INFERNOSTAFF_MORGANA","[T4-T8]2H_FIRE_RINGPAIR_AVALON","[T4-T8]MAIN_FIRESTAFF_CRYSTAL",
            #SACERDOTE
            "[T4-T8]MAIN_HOLYSTAFF","[T4-T8]2H_HOLYSTAFF","[T4-T8]2H_DIVINESTAFF","[T4-T8]MAIN_HOLYSTAFF_MORGANA",
            "[T4-T8]2H_HOLYSTAFF_HELL","[T4-T8]2H_HOLYSTAFF_UNDEAD","[T4-T8]MAIN_HOLYSTAFF_AVALON",
            "[T4-T8]2H_HOLYSTAFF_CRYSTAL",
            #ARCANO
            
         ],
        
        "guantes": [
            "[T4-T8]2H_KNUCKLES_SET1","[T4-T8]2H_KNUCKLES_SET2","[T4-T8]2H_KNUCKLES_SET3","[T4-T8]2H_KNUCKLES_SET3",
            "[T4-T8]2H_KNUCKLES_HELL"
         ],
        
        "armas": [
            "[T4-T8]MAIN_SWORD","[T4-T8]2H_DAGGERPAIR","[T4-T8]MAIN_AXE","[T4-T8]MAIN_1HCROSSBOW",
            "[T4-T8]2H_CROSSBOW","[T4-T8]2H_BOW","[T4-T8]2H_CLAYMORE","[T4-T8]MAIN_FIRESTAFF","[T4-T8]MAIN_HOLYSTAFF",
            "[T4-T8]2H_DUALSWORD","[T4-T8]2H_CURSEDSTAFF", "[T4-T8]2H_ARCANESTAFF",
            "[T4-T8]2H_AXE","[T4-T8]2H_SCYTHE_CRYSTAL","[T4-T8]2H_HALBERD","[T4-T8]2H_HALBERD_MORGANA",
        ],
        "escudos": [
            "[T4-T8]OFF_SHIELD","[T4-T8]OFF_TOWERSHIELD_UNDEAD","[T4-T8]OFF_SHIELD_HELL","[T4-T8]OFF_SPIKEDSHIELD_MORGANA",
            "[T4-T8]OFF_SHIELD_AVALON"
         ],
        "herramientas": [
            "[T4-T8]2H_TOOL_FISHINGROD","[T4-T8]2H_TOOL_KNIFE",
        ],
        "armaduras": [
            "[T4-T8]HEAD_LEATHER_SET1","[T4-T8]ARMOR_LEATHER_SET3","[T4-T8]SHOES_PLATE_SET1",
            "[T4-T8]ARMOR_LEATHER_SET1","[T4-T8]ARMOR_LEATHER_SET2","[T4-T8]BAG",
        ],
        "diarios": [
            "JOURNAL_FISHING_EMPTY"
        ],
    }

    @classmethod
    def get_categories(cls) -> list[str]:
        """Retorna la lista de categorías disponibles."""
        return list(cls.CATEGORIES.keys())

    @classmethod
    def get_items(cls, category: str) -> list[str]:
        """Retorna la lista de ítems para la categoría dada, o [] si no existe."""
        return list(cls.CATEGORIES.get(category, []))