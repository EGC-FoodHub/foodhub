import logging
import os

from app.modules.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


class FoodCheckerService:
    def __init__(self):
        self.hubfile_service = HubfileService()

    def _parse_food_content(self, content):
        """
        Analiza el contenido de un archivo .food con estructura YAML-like.
        """
        data = {}
        current_section = None
        valid_structure = False

        try:
            lines = content.split("\n")
            for line in lines:
                line = line.rstrip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("  ") or line.startswith("\t"):
                    if current_section and current_section in data:
                        key, value = line.strip().split(":", 1)
                        data[current_section][key.strip()] = value.strip()
                else:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        if not value:
                            current_section = key
                            data[current_section] = {}
                        else:
                            current_section = None
                            data[key] = value

            required_keys = ["name", "calories", "type"]
            if all(key in data for key in required_keys):
                valid_structure = True

            return {"valid": valid_structure, "data": data, "error": None}

        except Exception as e:
            return {"valid": False, "data": None, "error": f"Syntax error: {str(e)}"}

    def check_file_path(self, file_path):
        """Valida un archivo físico."""
        if not os.path.exists(file_path):
            return {"valid": False, "error": "File not found"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self._parse_food_content(content)
        except Exception as e:
            return {"valid": False, "error": f"Read error: {str(e)}"}

    def check_hubfile(self, file_id):
        """Valida un Hubfile ya subido."""
        hubfile = self.hubfile_service.get_or_404(file_id)
        path = self.hubfile_service.get_path_by_hubfile(hubfile)
        return self.check_file_path(path)

    def check_dataset(self, dataset):
        """Analiza todo el dataset."""
        summary = {"total_files": 0, "valid_files": 0, "total_calories": 0, "details": []}

        for food_model in dataset.files:
            for hubfile in food_model.files:
                summary["total_files"] += 1
                result = self.check_hubfile(hubfile.id)

                info = {
                    "filename": hubfile.name,
                    "valid": result["valid"],
                    "data": result.get("data"),
                    "error": result.get("error"),
                }

                if result["valid"]:
                    summary["valid_files"] += 1
                    try:
                        cal_str = result["data"].get("calories", "0").split()[0]
                        summary["total_calories"] += int(cal_str)
                    except:
                        pass

                summary["details"].append(info)

        return summary
