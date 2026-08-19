from transformer_design.models.enums import ConductorMaterial


def _temperature_color(temperature_c: float, minimum_c: float = 20.0, maximum_c: float = 140.0) -> str:
    """Map a screening temperature to a blue-yellow-red SVG color."""
    ratio = max(0.0, min(1.0, (temperature_c - minimum_c) / (maximum_c - minimum_c)))
    if ratio < 0.5:
        local = ratio * 2.0
        red = int(59 + (250 - 59) * local)
        green = int(130 + (204 - 130) * local)
        blue = int(246 + (21 - 246) * local)
    else:
        local = (ratio - 0.5) * 2.0
        red = int(250 + (220 - 250) * local)
        green = int(204 + (38 - 204) * local)
        blue = int(21 + (38 - 21) * local)
    return f"#{red:02x}{green:02x}{blue:02x}"


def generate_thermal_heatmap_svg(
    ambient_temperature_c: float,
    top_oil_temperature_c: float,
    hot_spot_temperature_c: float,
) -> str:
    """Render a compact, temperature-driven transformer cross-section."""
    ambient_color = _temperature_color(ambient_temperature_c)
    oil_color = _temperature_color(top_oil_temperature_c)
    winding_color = _temperature_color(hot_spot_temperature_c)
    return f"""
    <svg width="100%" viewBox="0 0 760 420" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="shadow"><feDropShadow dx="0" dy="6" stdDeviation="8" flood-opacity="0.18"/></filter>
      </defs>
      <rect width="760" height="420" rx="24" fill="#f8fafc"/>
      <rect x="75" y="55" width="610" height="310" rx="22" fill="{ambient_color}" opacity="0.24" stroke="#64748b" stroke-width="5"/>
      <rect x="92" y="100" width="576" height="248" rx="15" fill="{oil_color}" opacity="0.58"/>
      <g filter="url(#shadow)">
        <rect x="190" y="85" width="380" height="45" rx="8" fill="#475569"/>
        <rect x="190" y="290" width="380" height="45" rx="8" fill="#475569"/>
        <rect x="225" y="105" width="46" height="205" rx="5" fill="#64748b"/>
        <rect x="357" y="105" width="46" height="205" rx="5" fill="#64748b"/>
        <rect x="489" y="105" width="46" height="205" rx="5" fill="#64748b"/>
        <g fill="none" stroke="{winding_color}" stroke-width="24">
          <rect x="202" y="138" width="92" height="142" rx="28"/>
          <rect x="334" y="138" width="92" height="142" rx="28"/>
          <rect x="466" y="138" width="92" height="142" rx="28"/>
        </g>
      </g>
      <g font-family="Inter, system-ui, sans-serif" fill="#0f172a">
        <text x="105" y="82" font-size="17" font-weight="700">Dinamik Termal Kesit</text>
        <text x="105" y="386" font-size="15">Ortam: {ambient_temperature_c:.1f} °C</text>
        <text x="310" y="386" font-size="15">Üst yağ: {top_oil_temperature_c:.1f} °C</text>
        <text x="525" y="386" font-size="15" font-weight="700">Hot-spot: {hot_spot_temperature_c:.1f} °C</text>
      </g>
    </svg>
    """

def generate_transformer_svg(hv_mat, lv_mat, hv_turns, lv_turns, hv_area_mm2, lv_area_mm2, core_diameter_mm):
    """
    Üst düzey estetik, CSS animasyonlu, etkileşimli ve detaylı SVG üretir.
    Tank, yağ seviyesi, çekirdek sıkıştırma karkasları ve 3D gradient'ler içerir.
    """
    svg_w = 1000
    svg_h = 700
    
    # 1. Renk ve Materyal Ayarları
    copper_color = "#e65100" # Daha canlı bakır
    alum_color = "#94a3b8"   # Modern alüminyum grisi
    
    hv_color = copper_color if hv_mat == ConductorMaterial.COPPER else alum_color
    lv_color = copper_color if lv_mat == ConductorMaterial.COPPER else alum_color
    
    hv_name = "Bakır" if hv_mat == ConductorMaterial.COPPER else "Alüminyum"
    lv_name = "Bakır" if lv_mat == ConductorMaterial.COPPER else "Alüminyum"
    
    # 2. Geometrik Ölçeklemeler
    leg_w = max(40.0, min(120.0, core_diameter_mm / 2.5))
    lv_w = max(15.0, min(45.0, lv_area_mm2 / 8.0))
    hv_w = max(20.0, min(60.0, hv_area_mm2 / 1.5))
    gap = 8.0
    
    # Dinamik Faz Aralığı (Leg Spacing)
    leg_spacing = leg_w + 2*lv_w + 2*hv_w + 4*gap + 30.0
    leg_x = [240.0, 240.0 + leg_spacing, 240.0 + 2*leg_spacing]
    
    yoke_h = max(40.0, leg_w * 0.8)
    yoke_y = 120.0
    coil_h = 360.0
    coil_y = yoke_y + yoke_h + 10.0
    
    tank_margin = max(60.0, leg_w * 0.5)
    tank_x = leg_x[0] - leg_w/2 - lv_w - hv_w - gap*2 - tank_margin
    tank_y = 60.0 
    tank_w = (leg_x[2] + leg_w/2 + lv_w + hv_w + gap*2 + tank_margin) - tank_x
    tank_h = 580.0
    
    # Yağ seviyesi
    oil_y = tank_y + 80
    oil_h = tank_h - 80
    
    # 3. Desenler
    hv_pattern_size = max(4.0, min(20.0, 100000.0 / (hv_turns + 1.0)))
    lv_pattern_size = max(4.0, min(20.0, 10000.0 / (lv_turns + 1.0)))
    
    # Hover CSS Dynamic
    dynamic_css = ""
    
    layer_bg = ""
    layer_core = ""
    layer_frame = ""
    layer_coils = ""
    layer_text = ""
    layer_tooltips = ""
    
    layer_bg += f'''
        <!-- Arka Plan Tank ve Yag -->
        <g id="tank_trigger" class="interactive">
            <rect class="tank-bg" x="{tank_x}" y="{tank_y}" width="{tank_w}" height="{tank_h}" />
            <rect class="oil-bg" x="{tank_x + 4}" y="{oil_y}" width="{tank_w - 8}" height="{oil_h - 4}" rx="6px" />
            <line class="oil-wave" x1="{tank_x + 10}" y1="{oil_y}" x2="{tank_x + tank_w - 10}" y2="{oil_y}" />
        </g>
    '''
    
    dynamic_css += "#tank_trigger:hover ~ #tank_tooltip { visibility: visible; opacity: 1; }\n"
    layer_tooltips += f'''
        <g id="tank_tooltip" class="tooltip" transform="translate({tank_x + tank_w/2}, {tank_y + 30})">
            <rect class="tooltip-bg" x="-100" y="-20" width="200" height="40" />
            <text class="tooltip-title" x="0" y="5" text-anchor="middle">Transformatör Ana Tankı</text>
        </g>
    '''
    
    layer_core += f'''
        <!-- Ust ve Alt Yoke -->
        <g id="yoke_trigger" class="interactive">
            <rect class="shape core-steel" x="{leg_x[0] - leg_w/2}" y="{yoke_y}" width="{leg_x[2] - leg_x[0] + leg_w}" height="{yoke_h}" />
            <rect class="shape core-steel" x="{leg_x[0] - leg_w/2}" y="{yoke_y + 420}" width="{leg_x[2] - leg_x[0] + leg_w}" height="{yoke_h}" />
        </g>
        <path class="flux-line" d="M {leg_x[0]} {yoke_y + yoke_h/2} L {leg_x[1]} {yoke_y + yoke_h/2} L {leg_x[1]} {yoke_y + 420 + yoke_h/2} L {leg_x[0]} {yoke_y + 420 + yoke_h/2} Z" />
        <path class="flux-line" d="M {leg_x[1]} {yoke_y + yoke_h/2} L {leg_x[2]} {yoke_y + yoke_h/2} L {leg_x[2]} {yoke_y + 420 + yoke_h/2} L {leg_x[1]} {yoke_y + 420 + yoke_h/2} Z" />
    '''
    
    dynamic_css += "#yoke_trigger:hover ~ #yoke_tooltip { visibility: visible; opacity: 1; }\n"
    layer_tooltips += f'''
        <g id="yoke_tooltip" class="tooltip" transform="translate({leg_x[1]}, {yoke_y - 30})">
            <rect class="tooltip-bg" x="-120" y="-40" width="240" height="60" />
            <text class="tooltip-title" x="0" y="-20" text-anchor="middle">Manyetik Boyunduruk</text>
            <text class="tooltip-text" x="0" y="0" text-anchor="middle">Faz Aralığı: {leg_spacing:.1f} mm</text>
        </g>
    '''
    
    layer_frame += f'''
        <!-- Karkas -->
        <rect class="frame" x="{leg_x[0] - leg_w - 20}" y="{yoke_y - 20}" width="{leg_x[2] - leg_x[0] + 2*leg_w + 40}" height="30" rx="4" />
        <rect class="frame" x="{leg_x[0] - leg_w - 20}" y="{yoke_y + 420 + yoke_h - 10}" width="{leg_x[2] - leg_x[0] + 2*leg_w + 40}" height="30" rx="4" />
    '''
    
    for i, lx in enumerate(leg_x):
        phase_letter = ["U", "V", "W"][i]
        c_x = lx - leg_w/2
        
        lv_left_x = c_x - gap - lv_w
        lv_right_x = c_x + leg_w + gap
        hv_left_x = lv_left_x - gap - hv_w
        hv_right_x = lv_right_x + lv_w + gap
        
        # Bacak
        layer_core += f'''
        <g id="core_{i}_trigger" class="interactive">
            <rect class="shape core-steel" x="{c_x}" y="{yoke_y + yoke_h}" width="{leg_w}" height="{420 - yoke_h}" />
        </g>
        '''
        dynamic_css += f"#core_{i}_trigger:hover ~ #core_{i}_tooltip {{ visibility: visible; opacity: 1; }}\n"
        layer_tooltips += f'''
        <g id="core_{i}_tooltip" class="tooltip" transform="translate({lx}, {yoke_y + yoke_h + 30})">
            <rect class="tooltip-bg" x="-90" y="-40" width="180" height="60" />
            <text class="tooltip-title" x="0" y="-20" text-anchor="middle">Faz {phase_letter} Çekirdek</text>
            <text class="tooltip-text" x="0" y="0" text-anchor="middle">Çap (D): {core_diameter_mm:.1f} mm</text>
        </g>
        '''
            
        # LV Sargısı
        layer_coils += f'''
        <g id="lv_{i}_trigger" class="interactive">
            <rect class="shape lv-coil" x="{lv_left_x}" y="{coil_y}" width="{lv_w}" height="{coil_h}" rx="3" />
            <rect class="shape lv-coil" x="{lv_right_x}" y="{coil_y}" width="{lv_w}" height="{coil_h}" rx="3" />
        </g>
        '''
        dynamic_css += f"#lv_{i}_trigger:hover ~ #lv_{i}_tooltip {{ visibility: visible; opacity: 1; }}\n"
        layer_tooltips += f'''
        <g id="lv_{i}_tooltip" class="tooltip" transform="translate({lx}, {coil_y + coil_h/2})">
            <rect class="tooltip-bg" x="-130" y="-55" width="260" height="110" />
            <text class="tooltip-title" x="0" y="-30" text-anchor="middle">Faz {phase_letter} - LV Sargısı</text>
            <text class="tooltip-text" x="0" y="-10" text-anchor="middle">Malzeme: <tspan class="tooltip-accent">{lv_name}</tspan> | {lv_turns} Tur</text>
            <text class="tooltip-text" x="0" y="10" text-anchor="middle">Kesit Alanı: {lv_area_mm2:.1f} mm²</text>
            <text class="tooltip-text" x="0" y="30" text-anchor="middle">Genişlik: {lv_w:.1f}mm | Yükseklik: {coil_h:.0f}mm</text>
        </g>
        '''
        
        # HV Sargısı
        layer_coils += f'''
        <g id="hv_{i}_trigger" class="interactive">
            <rect class="shape hv-coil" x="{hv_left_x}" y="{coil_y + 15}" width="{hv_w}" height="{coil_h - 30}" rx="4" />
            <rect class="shape hv-coil" x="{hv_right_x}" y="{coil_y + 15}" width="{hv_w}" height="{coil_h - 30}" rx="4" />
        </g>
        '''
        dynamic_css += f"#hv_{i}_trigger:hover ~ #hv_{i}_tooltip {{ visibility: visible; opacity: 1; }}\n"
        layer_tooltips += f'''
        <g id="hv_{i}_tooltip" class="tooltip" transform="translate({lx}, {coil_y + coil_h/2 + 50})">
            <rect class="tooltip-bg" x="-130" y="-55" width="260" height="110" />
            <text class="tooltip-title" x="0" y="-30" text-anchor="middle">Faz {phase_letter} - HV Sargısı</text>
            <text class="tooltip-text" x="0" y="-10" text-anchor="middle">Malzeme: <tspan class="tooltip-accent">{hv_name}</tspan> | {hv_turns} Tur</text>
            <text class="tooltip-text" x="0" y="10" text-anchor="middle">Kesit Alanı: {hv_area_mm2:.1f} mm²</text>
            <text class="tooltip-text" x="0" y="30" text-anchor="middle">Genişlik: {hv_w:.1f}mm | Yükseklik: {coil_h-30:.0f}mm</text>
        </g>
        '''
        
    css = f'''
    <style>
        .tank-bg {{ fill: #f1f5f9; stroke: #94a3b8; stroke-width: 4px; rx: 10px; }}
        .oil-bg {{ fill: #fef3c7; opacity: 0.5; }}
        .oil-wave {{ stroke: #fde68a; stroke-width: 2px; stroke-dasharray: 10, 5; }}
        .core-steel {{ fill: url(#coreGradient); stroke: #334155; stroke-width: 2px; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3)); transition: 0.3s; }}
        .frame {{ fill: url(#frameGradient); stroke: #1e293b; stroke-width: 2px; }}
        
        .hv-coil {{ fill: url(#hvPattern); stroke: #1e293b; stroke-width: 1.5px; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.4)); transition: all 0.3s ease; cursor: pointer; }}
        .lv-coil {{ fill: url(#lvPattern); stroke: #1e293b; stroke-width: 1.5px; filter: drop-shadow(1px 1px 3px rgba(0,0,0,0.4)); transition: all 0.3s ease; cursor: pointer; }}
        
        .interactive:hover .shape {{ filter: brightness(1.15) drop-shadow(0px 0px 12px rgba(255,255,255,0.6)); stroke: #fff; }}
        .interactive:hover .tank-bg {{ filter: brightness(0.95); stroke: #64748b; }}
        
        .tooltip {{
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none; /* Tooltip ustune gelince titremeyi onler */
        }}
        
        {dynamic_css}
        
        .tooltip-bg {{ fill: rgba(255, 255, 255, 0.98); stroke: #cbd5e1; stroke-width: 1.5px; rx: 6px; filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.15)); }}
        .tooltip-title {{ fill: #0f172a; font-family: 'Segoe UI', sans-serif; font-size: 14px; font-weight: bold; }}
        .tooltip-text {{ fill: #475569; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
        .tooltip-accent {{ fill: #2563eb; font-weight: bold; }}
        
        .flux-line {{ stroke: #38bdf8; stroke-width: 2px; stroke-dasharray: 8, 4; fill: none; opacity: 0; pointer-events: none; }}
        @keyframes fluxFlow {{ to {{ stroke-dashoffset: -24; }} }}
        .interactive:hover + .flux-line, .interactive:hover ~ .flux-line {{
            opacity: 0.6;
            animation: fluxFlow 1s linear infinite;
        }}
    </style>
    '''
    
    svg_w = max(1000.0, tank_x + tank_w + 50.0)
    svg_h = max(700.0, tank_y + tank_h + 50.0)

    svg = f'''
    <svg width="100%" height="100%" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">
        {css}
        <defs>
            <linearGradient id="coreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#94a3b8" />
                <stop offset="20%" stop-color="#cbd5e1" />
                <stop offset="50%" stop-color="#f8fafc" />
                <stop offset="80%" stop-color="#94a3b8" />
                <stop offset="100%" stop-color="#64748b" />
            </linearGradient>
            
            <linearGradient id="frameGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#475569" />
                <stop offset="50%" stop-color="#1e293b" />
                <stop offset="100%" stop-color="#0f172a" />
            </linearGradient>
            
            <pattern id="hvPattern" x="0" y="0" width="{hv_pattern_size}" height="{hv_pattern_size}" patternUnits="userSpaceOnUse">
                <rect width="{hv_pattern_size}" height="{hv_pattern_size}" fill="{hv_color}" />
                <circle cx="{{hv_pattern_size/2}}" cy="{{hv_pattern_size/2}}" r="{max(1.0, hv_pattern_size/4)}" fill="#ffffff" opacity="0.3"/>
                <path d="M 0 {hv_pattern_size} L {hv_pattern_size} 0" stroke="#000" stroke-width="0.5" opacity="0.2"/>
            </pattern>
            
            <pattern id="lvPattern" x="0" y="0" width="{lv_pattern_size}" height="{lv_pattern_size}" patternUnits="userSpaceOnUse">
                <rect width="{lv_pattern_size}" height="{lv_pattern_size}" fill="{lv_color}" />
                <rect x="0" y="{{lv_pattern_size/2}}" width="{lv_pattern_size}" height="{max(1.0, lv_pattern_size/3)}" fill="#ffffff" opacity="0.4"/>
            </pattern>
        </defs>
        
        {layer_bg}
        {layer_core}
        {layer_frame}
        {layer_coils}
        {layer_text}
        
        <!-- TOOLTIPS EN USTTE (Z-INDEX) -->
        {layer_tooltips}
    </svg>
    '''

    return svg
