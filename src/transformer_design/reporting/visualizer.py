import math
from transformer_design.models.enums import ConductorMaterial

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
    leg_spacing = 260
    leg_x = [240, 240 + leg_spacing, 240 + 2*leg_spacing] # 240, 500, 760
    
    leg_w = max(40.0, min(90.0, core_diameter_mm / 2.5))
    lv_w = max(15.0, min(35.0, lv_area_mm2 / 8.0))
    hv_w = max(20.0, min(50.0, hv_area_mm2 / 1.5))
    gap = 6.0
    yoke_h = 70.0
    
    coil_h = 360.0
    coil_y = 150.0
    
    tank_margin = 80
    tank_x = leg_x[0] - leg_w/2 - lv_w - hv_w - gap*2 - tank_margin
    tank_y = 40
    tank_w = (leg_x[2] + leg_w/2 + lv_w + hv_w + gap*2 + tank_margin) - tank_x
    tank_h = 600
    
    # Yağ seviyesi (tankın %85'i dolu)
    oil_y = tank_y + 80
    oil_h = tank_h - 80
    
    # 3. Desenler
    hv_pattern_size = max(4.0, min(20.0, 100000.0 / (hv_turns + 1.0)))
    lv_pattern_size = max(4.0, min(20.0, 10000.0 / (lv_turns + 1.0)))
    
    css = f"""
    <style>
        .tank-bg {{ fill: #f1f5f9; stroke: #94a3b8; stroke-width: 4px; rx: 10px; }}
        .oil-bg {{ fill: #fef3c7; opacity: 0.5; }}
        .oil-wave {{ stroke: #fde68a; stroke-width: 2px; stroke-dasharray: 10, 5; }}
        .core-steel {{ fill: url(#coreGradient); stroke: #334155; stroke-width: 2px; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3)); transition: 0.3s; }}
        .frame {{ fill: url(#frameGradient); stroke: #1e293b; stroke-width: 2px; }}
        
        .hv-coil {{ fill: url(#hvPattern); stroke: #1e293b; stroke-width: 1.5px; filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.4)); transition: all 0.3s ease; cursor: pointer; }}
        .lv-coil {{ fill: url(#lvPattern); stroke: #1e293b; stroke-width: 1.5px; filter: drop-shadow(1px 1px 3px rgba(0,0,0,0.4)); transition: all 0.3s ease; cursor: pointer; }}
        
        .interactive:hover .shape {{ filter: brightness(1.15) drop-shadow(0px 0px 12px rgba(255,255,255,0.6)); stroke: #fff; }}
        
        .flux-line {{
            fill: none;
            stroke: #3b82f6;
            stroke-width: 4px;
            stroke-dasharray: 20, 15;
            opacity: 0.6;
            animation: flow 2s linear infinite;
        }}
        @keyframes flow {{
            from {{ stroke-dashoffset: 35; }}
            to {{ stroke-dashoffset: 0; }}
        }}
        
        /* Tooltip Container */
        .tooltip {{
            visibility: hidden;
            opacity: 0;
            transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .interactive:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        .tooltip-bg {{ fill: rgba(15, 23, 42, 0.95); rx: 8px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.5)); stroke: #38bdf8; stroke-width: 1px; }}
        .tooltip-text {{ fill: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; font-size: 13px; }}
        .tooltip-title {{ fill: #38bdf8; font-family: 'Segoe UI', system-ui, sans-serif; font-size: 15px; font-weight: 700; }}
        .tooltip-accent {{ fill: #fbbf24; font-weight: bold; }}
        
        .dim-line {{ stroke: #475569; stroke-width: 1.5px; stroke-dasharray: 4, 4; }}
        .dim-text {{ fill: #1e293b; font-family: 'Consolas', monospace; font-size: 14px; font-weight: bold; text-anchor: middle; background: white; }}
        .label-text {{ fill: #64748b; font-family: sans-serif; font-size: 14px; font-weight: bold; }}
    </style>
    """
    
    svg = f"""
    <svg width="100%" height="100%" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">
        {css}
        <defs>
            <!-- 3D Metalic Gradients -->
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
                <circle cx="{hv_pattern_size/2}" cy="{hv_pattern_size/2}" r="{max(1.0, hv_pattern_size/4)}" fill="#ffffff" opacity="0.3"/>
                <path d="M 0 {hv_pattern_size} L {hv_pattern_size} 0" stroke="#000" stroke-width="0.5" opacity="0.2"/>
            </pattern>
            
            <pattern id="lvPattern" x="0" y="0" width="{lv_pattern_size}" height="{lv_pattern_size}" patternUnits="userSpaceOnUse">
                <rect width="{lv_pattern_size}" height="{lv_pattern_size}" fill="{lv_color}" />
                <rect x="0" y="{lv_pattern_size/2}" width="{lv_pattern_size}" height="{max(1.0, lv_pattern_size/3)}" fill="#ffffff" opacity="0.4"/>
            </pattern>
            
            <marker id="arrow-start" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 10 0 L 0 5 L 10 10 z" fill="#475569" />
            </marker>
            <marker id="arrow-end" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
            </marker>
        </defs>

        <!-- Arka Plan Tank ve Yağ -->
        <rect class="tank-bg" x="{tank_x}" y="{tank_y}" width="{tank_w}" height="{tank_h}" />
        <rect class="oil-bg" x="{tank_x + 4}" y="{oil_y}" width="{tank_w - 8}" height="{oil_h - 4}" rx="6px" />
        <line class="oil-wave" x1="{tank_x + 10}" y1="{oil_y}" x2="{tank_x + tank_w - 10}" y2="{oil_y}" />
        <text class="label-text" x="{tank_x + 20}" y="{oil_y - 10}">İzolasyon Yağ Seviyesi</text>
        <text class="label-text" x="{tank_x + 20}" y="{tank_y + 30}">Transformatör Ana Tankı</text>

        <!-- Karkas (Frame) Üst ve Alt -->
        <rect class="frame" x="{leg_x[0] - leg_w - 20}" y="{90 - 20}" width="{leg_x[2] - leg_x[0] + 2*leg_w + 40}" height="30" rx="4" />
        <rect class="frame" x="{leg_x[0] - leg_w - 20}" y="{510 + yoke_h}" width="{leg_x[2] - leg_x[0] + 2*leg_w + 40}" height="30" rx="4" />

        <!-- Üst ve Alt Yoke -->
        <g class="interactive">
            <rect class="shape core-steel" x="{leg_x[0] - leg_w/2}" y="90" width="{leg_x[2] - leg_x[0] + leg_w}" height="{yoke_h}" />
            <rect class="shape core-steel" x="{leg_x[0] - leg_w/2}" y="510" width="{leg_x[2] - leg_x[0] + leg_w}" height="{yoke_h}" />
            <g class="tooltip" transform="translate(500, 45)">
                <rect class="tooltip-bg" x="-120" y="-40" width="240" height="40" />
                <text class="tooltip-title" x="0" y="-15" text-anchor="middle">Manyetik Çekirdek (Boyunduruk)</text>
            </g>
        </g>
        
        <!-- Manyetik Akı (Flux) Animasyonu -->
        <path class="flux-line" d="M {leg_x[0]} {90 + yoke_h/2} L {leg_x[1]} {90 + yoke_h/2} L {leg_x[1]} {510 + yoke_h/2} L {leg_x[0]} {510 + yoke_h/2} Z" />
        <path class="flux-line" d="M {leg_x[1]} {90 + yoke_h/2} L {leg_x[2]} {90 + yoke_h/2} L {leg_x[2]} {510 + yoke_h/2} L {leg_x[1]} {510 + yoke_h/2} Z" />
        
        <!-- Ölçü Çizgileri (Genel) -->
        <line class="dim-line" x1="{leg_x[0]}" y1="50" x2="{leg_x[1]}" y2="50" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
        <text class="dim-text" x="{(leg_x[0]+leg_x[1])/2}" y="40">Faz Aralığı: {leg_spacing}mm</text>
        
        <line class="dim-line" x1="{tank_x - 30}" y1="{coil_y}" x2="{tank_x - 30}" y2="{coil_y + coil_h}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
        <text class="dim-text" x="{tank_x - 40}" y="{coil_y + coil_h/2}" transform="rotate(-90 {tank_x - 40} {coil_y + coil_h/2})">Sargı Yüksekliği (Hw)</text>

    """
    
    # 3 Bacağı ve sargılarını (Kesit görünümü) çiz
    for i, lx in enumerate(leg_x):
        phase_letter = ["U", "V", "W"][i]
        
        c_x = lx - leg_w/2
        
        lv_left_x = c_x - gap - lv_w
        lv_right_x = c_x + leg_w + gap
        
        hv_left_x = lv_left_x - gap - hv_w
        hv_right_x = lv_right_x + lv_w + gap
        
        svg += f"""
        <!-- Faz {phase_letter} Çelik Bacak -->
        <g class="interactive">
            <rect class="shape core-steel" x="{c_x}" y="{90 + yoke_h}" width="{leg_w}" height="{510 - (90 + yoke_h)}" />
            <g class="tooltip" transform="translate({lx}, {90 + yoke_h + 30})">
                <rect class="tooltip-bg" x="-100" y="-30" width="200" height="30" />
                <text class="tooltip-text" x="0" y="-10" text-anchor="middle">Faz {phase_letter} Çekirdek Bacağı</text>
            </g>
        </g>
        
        <!-- Faz {phase_letter} LV Sargısı -->
        <g class="interactive">
            <rect class="shape lv-coil" x="{lv_left_x}" y="{coil_y}" width="{lv_w}" height="{coil_h}" rx="3" />
            <rect class="shape lv-coil" x="{lv_right_x}" y="{coil_y}" width="{lv_w}" height="{coil_h}" rx="3" />
            
            <g class="tooltip" transform="translate({lx}, {coil_y - 25})">
                <rect class="tooltip-bg" x="-130" y="-75" width="260" height="70" />
                <text class="tooltip-title" x="0" y="-50" text-anchor="middle">LV Sargısı (Alçak Gerilim)</text>
                <text class="tooltip-text" x="0" y="-30" text-anchor="middle">Malzeme: <tspan class="tooltip-accent">{lv_name}</tspan> | {lv_turns} Tur</text>
                <text class="tooltip-text" x="0" y="-10" text-anchor="middle">Kesit Alanı: {lv_area_mm2:.1f} mm²</text>
            </g>
        </g>
        
        <!-- Faz {phase_letter} HV Sargısı -->
        <g class="interactive">
            <rect class="shape hv-coil" x="{hv_left_x}" y="{coil_y + 15}" width="{hv_w}" height="{coil_h - 30}" rx="4" />
            <rect class="shape hv-coil" x="{hv_right_x}" y="{coil_y + 15}" width="{hv_w}" height="{coil_h - 30}" rx="4" />
            
            <g class="tooltip" transform="translate({lx}, {coil_y + coil_h + 40})">
                <rect class="tooltip-bg" x="-130" y="-10" width="260" height="70" />
                <text class="tooltip-title" x="0" y="15" text-anchor="middle">HV Sargısı (Yüksek Gerilim)</text>
                <text class="tooltip-text" x="0" y="35" text-anchor="middle">Malzeme: <tspan class="tooltip-accent">{hv_name}</tspan> | {hv_turns} Tur</text>
                <text class="tooltip-text" x="0" y="55" text-anchor="middle">Kesit Alanı: {hv_area_mm2:.1f} mm²</text>
            </g>
        </g>
        """
        
        if i == 1:
            # Çekirdek Çapı Ölçüsü
            svg += f"""
            <line class="dim-line" x1="{c_x}" y1="{coil_y + coil_h/2}" x2="{c_x + leg_w}" y2="{coil_y + coil_h/2}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
            <text class="dim-text" x="{lx}" y="{coil_y + coil_h/2 - 8}">D={core_diameter_mm:.1f}mm</text>
            """
            
            # LV / HV Label
            svg += f"""
            <line class="dim-line" x1="{lv_right_x}" y1="{coil_y + 30}" x2="{lv_right_x + lv_w}" y2="{coil_y + 30}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
            <text class="dim-text" x="{lv_right_x + lv_w/2}" y="{coil_y + 20}">LV</text>
            
            <line class="dim-line" x1="{hv_right_x}" y1="{coil_y + 70}" x2="{hv_right_x + hv_w}" y2="{coil_y + 70}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
            <text class="dim-text" x="{hv_right_x + hv_w/2}" y="{coil_y + 60}">HV</text>
            
            <line class="dim-line" x1="{lv_right_x + lv_w}" y1="{coil_y + 110}" x2="{hv_right_x}" y2="{coil_y + 110}" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
            <text class="dim-text" x="{lv_right_x + lv_w + gap/2}" y="{coil_y + 100}">Gap</text>
            """

    # Legend / Info Box (Sol alt köşe)
    svg += f"""
        <g transform="translate({tank_x + 20}, {tank_y + tank_h - 120})">
            <rect fill="#ffffff" opacity="0.8" width="220" height="90" rx="5" stroke="#94a3b8" stroke-width="1.5" />
            <text x="10" y="25" fill="#1e293b" font-weight="bold" font-family="sans-serif">Malzeme Lejantı</text>
            
            <rect x="10" y="40" width="15" height="15" fill="{copper_color}" rx="3" />
            <text x="35" y="52" fill="#475569" font-family="sans-serif">Bakır İletken</text>
            
            <rect x="10" y="65" width="15" height="15" fill="{alum_color}" rx="3" />
            <text x="35" y="77" fill="#475569" font-family="sans-serif">Alüminyum İletken</text>
        </g>
    </svg>
    """
    
    return svg
