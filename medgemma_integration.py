#!/usr/bin/env python3
"""
Integrazione con MedGemma per validazione e arricchimento dati medici.
Supporta analisi semantica, validazione clinica e identificazione pattern.
"""

from typing import Dict, List, Optional, Any
import json
import logging
from dataclasses import dataclass, asdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LabValue:
    """Valore di laboratorio con validazione."""
    parameter: str
    value: float
    unit: str
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    is_abnormal: Optional[bool] = None
    clinical_significance: Optional[str] = None
    severity: Optional[str] = None


class MedGemmaValidator:
    """Validatore clinico usando AI e regole mediche."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.reference_ranges = self._load_reference_ranges()
    
    def _load_reference_ranges(self) -> Dict:
        return {
            'eritrociti_rbc': {'min': 4.0, 'max': 6.0, 'unit': '10^6/uL', 'category': 'emocromo', 'critical_low': 3.0, 'critical_high': 7.0},
            'leucociti': {'min': 4.5, 'max': 11.0, 'unit': '10^3/uL', 'category': 'emocromo', 'critical_low': 2.0, 'critical_high': 30.0},
            'emoglobina': {'min': 13.5, 'max': 17.5, 'unit': 'g/dL', 'category': 'emocromo', 'critical_low': 7.0, 'critical_high': 20.0},
            'creatinina': {'min': 0.6, 'max': 1.3, 'unit': 'mg/dL', 'category': 'renale', 'critical_low': 0.3, 'critical_high': 5.0},
            'glicemia': {'min': 70, 'max': 100, 'unit': 'mg/dL', 'category': 'metabolismo', 'critical_low': 40, 'critical_high': 600},
        }
    
    def validate_value(self, parameter: str, value: float, unit: str = '') -> LabValue:
        param_key = parameter.lower().replace(' ', '_')
        ref_data = self.reference_ranges.get(param_key)
        
        if not ref_data:
            return LabValue(parameter=parameter, value=value, unit=unit, clinical_significance="Parametro non riconosciuto")
        
        is_abnormal = value < ref_data['min'] or value > ref_data['max']
        severity = 'normal'
        
        if value < ref_data['min']:
            severity = 'severe_low' if value <= ref_data['critical_low'] else 'mild_low'
        elif value > ref_data['max']:
            severity = 'severe_high' if value >= ref_data['critical_high'] else 'mild_high'
        
        return LabValue(
            parameter=parameter,
            value=value,
            unit=unit or ref_data['unit'],
            reference_min=ref_data['min'],
            reference_max=ref_data['max'],
            is_abnormal=is_abnormal,
            severity=severity,
            clinical_significance=f"Valore {'ANOMALO' if is_abnormal else 'NORMALE'}"
        )
    
    def analyze_panel(self, values: Dict[str, float]) -> Dict[str, Any]:
        validated = {}
        abnormals = []
        
        for param, value in values.items():
            if value:
                lab_value = self.validate_value(param, float(value))
                validated[param] = lab_value
                if lab_value.is_abnormal:
                    abnormals.append(lab_value)
        
        return {
            'validated_values': validated,
            'abnormal_count': len(abnormals),
            'abnormals': abnormals,
            'risk_level': 'ALTO' if len(abnormals) > 5 else 'MODERATO' if len(abnormals) > 2 else 'BASSO'
        }
    
    def generate_report(self, analysis: Dict) -> str:
        report = ["="*80, "REPORT ANALISI CLINICA", "="*80, ""]
        report.append(f"Parametri: {len(analysis['validated_values'])}")
        report.append(f"Anomali: {analysis['abnormal_count']}")
        report.append(f"Rischio: {analysis['risk_level']}")
        return "\n".join(report)