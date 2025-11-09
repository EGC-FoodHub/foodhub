import os


class FoodHandler:
    """
    Analizador para archivos .food (recetas en texto plano).
    Convención: líneas que empiezan por 'ingredient:' o 'step:'.
    """

    def parse_food(self, file_path: str) -> dict:
        """Lee y analiza un archivo .food devolviendo un diccionario estructurado."""
        if not file_path.lower().endswith(".food") or not os.path.exists(file_path):
            return {}

        recipe = {"name": None, "author": None, "ingredients": [], "steps": []}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("name:"):
                        recipe["name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("author:"):
                        recipe["author"] = line.split(":", 1)[1].strip()
                    elif line.startswith("ingredient:"):
                        recipe["ingredients"].append(line.split(":", 1)[1].strip())
                    elif line.startswith("step:"):
                        recipe["steps"].append(line.split(":", 1)[1].strip())
        except Exception as e:
            print(f"[FoodHandler] Error parsing {file_path}: {e}")
            return {}

        recipe["ingredient_count"] = len(recipe["ingredients"])
        recipe["step_count"] = len(recipe["steps"])
        return recipe

    def summarize_dataset(self, dataset) -> dict:
        """Analiza todos los archivos .food en un dataset y devuelve métricas agregadas."""
        total_recipes = 0
        total_ingredients = 0
        all_recipes = []

        for fm in dataset.feature_models:
            for file in fm.files:
                if file.name.lower().endswith(".food"):
                    file_path = file.get_path()
                    data = self.parse_food(file_path)
                    if data:
                        total_recipes += 1
                        total_ingredients += data.get("ingredient_count", 0)
                        all_recipes.append(data)

        return {"total_recipes": total_recipes, "total_ingredients": total_ingredients, "recipes": all_recipes}
