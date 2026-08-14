from typing import Callable, Dict, Any, List
import itertools

def run_grid_search_optimizer(
    base_calc_func: Callable,
    objective: str = "toc"
) -> Dict[str, Any]:
    
    best_value = float('inf')
    best_params = None
    best_result = None
    
    # Kısıtlı aralık: Çok büyük aralık Streamlit'i dondurabilir.
    j_range = [2.0, 2.5, 3.0]
    b_range = [1.50, 1.60, 1.65, 1.70]
    
    # Callback (flux_T, hv_j, lv_j) -> (toc, total_cost)
    for flux, hv_j, lv_j in itertools.product(b_range, j_range, j_range):
        try:
            res = base_calc_func(flux, hv_j, lv_j)
            
            val = res["toc_usd"] if objective == "toc" else res["total_factory_cost"]
            
            if val < best_value:
                best_value = val
                best_params = {"flux_T": flux, "hv_j": hv_j, "lv_j": lv_j}
                best_result = res
                
        except Exception:
            continue
            
    if best_params is None:
        raise ValueError("Hiçbir geçerli tasarım bulunamadı.")
        
    return {
        "best_value": best_value,
        "best_parameters": best_params,
        "best_result": best_result
    }
