import os


class FoodHandler:
    """
    Analizador para archivos .food en formato similar a YAML.
    Maneja información nutricional de alimentos.
    """

    def parse_food(self, file_path: str) -> dict:
        """Lee y analiza un archivo .food devolviendo un diccionario estructurado."""
        if not file_path.lower().endswith(".food") or not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.readlines()

            food_data = {"name": "", "calories": "", "type": "", "nutritional_values": {}}

            current_section = None

            for line in content:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if line == "nutritional_values:":
                    current_section = "nutritional_values"
                    continue

                # Procesar líneas clave-valor
                if ":" in line and current_section != "nutritional_values":
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "name":
                        food_data["name"] = value
                    elif key == "calories":
                        food_data["calories"] = value
                    elif key == "type":
                        food_data["type"] = value

                elif current_section == "nutritional_values" and ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    food_data["nutritional_values"][key] = value

            return food_data

        except Exception as e:
            print(f"[FoodHandler] Error reading {file_path}: {e}")
            return {}

    def summarize_dataset(self, dataset) -> dict:
        """Analiza todos los archivos .food en un dataset y devuelve métricas agregadas."""
        total_foods = 0
        total_calories = 0
        type_distribution = {}
        all_foods = []
        nutritional_totals = {}

        for fm in dataset.feature_models:
            for file in fm.files:
                if file.name.lower().endswith(".food"):
                    file_path = file.get_path()
                    data = self.parse_food(file_path)
                    if data and data.get("name"):
                        total_foods += 1

                        # Extraer calorías numéricas para cálculos
                        calories_str = data.get("calories", "0 kcal")
                        try:
                            calories = int(calories_str.split()[0])
                            total_calories += calories
                        except (ValueError, IndexError):
                            pass

                        # Distribución por tipo
                        food_type = data.get("type", "UNKNOWN")
                        type_distribution[food_type] = type_distribution.get(food_type, 0) + 1

                        # Acumular valores nutricionales
                        nutritional_values = data.get("nutritional_values", {})
                        for nutrient, value in nutritional_values.items():
                            if nutrient not in nutritional_totals:
                                nutritional_totals[nutrient] = []
                            nutritional_totals[nutrient].append(value)

                        all_foods.append(data)

        # Calcular promedios nutricionales
        nutritional_averages = {}
        for nutrient, values in nutritional_totals.items():
            # Para valores numéricos con unidades, extraer solo el número
            numeric_values = []
            for value in values:
                if isinstance(value, str):
                    try:
                        # Extraer número de strings como "15g", "25%", etc.
                        # Manejar diferentes formatos: "15g", "25%", "2.3g", etc.
                        num_part = value.split()[0] if " " in value else value
                        # Remover caracteres no numéricos excepto punto decimal
                        num_str = ""
                        for char in num_part:
                            if char.isdigit() or char == ".":
                                num_str += char
                        if num_str:
                            numeric_values.append(float(num_str))
                    except (ValueError, IndexError):
                        continue
                elif isinstance(value, (int, float)):
                    numeric_values.append(value)

            if numeric_values:
                nutritional_averages[nutrient] = sum(numeric_values) / len(numeric_values)

        return {
            "total_foods": total_foods,
            "total_calories": total_calories,
            "average_calories": total_calories / total_foods if total_foods > 0 else 0,
            "type_distribution": type_distribution,
            "nutritional_averages": nutritional_averages,
            "foods": all_foods,
        }

    def get_food_details(self, file_path: str) -> dict:
        """Obtiene detalles específicos de un archivo .food"""
        data = self.parse_food(file_path)
        if not data:
            return {}

        # Procesar calorías como número
        calories_num = 0
        try:
            calories_str = data.get("calories", "0 kcal")
            calories_num = int(calories_str.split()[0])
        except (ValueError, IndexError):
            pass

        # Procesar valores nutricionales como números
        numeric_nutritional = {}
        for nutrient, value in data.get("nutritional_values", {}).items():
            try:
                if isinstance(value, str):
                    num_part = value.split()[0] if " " in value else value
                    num_str = ""
                    for char in num_part:
                        if char.isdigit() or char == ".":
                            num_str += char
                    if num_str:
                        numeric_nutritional[nutrient] = float(num_str)
            except (ValueError, IndexError):
                continue

        return {
            "name": data.get("name", ""),
            "calories": calories_num,
            "calories_display": data.get("calories", ""),
            "type": data.get("type", ""),
            "nutritional_values": data.get("nutritional_values", {}),
            "numeric_nutritional": numeric_nutritional,
        }
