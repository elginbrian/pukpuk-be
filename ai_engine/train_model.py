import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
import random
import os

# --- 1. KONFIGURASI ---
MODEL_PATH = "../app/infrastructure/ml_models/pukpuk_demand_v1.cbm"
# Pastikan folder tujuan ada
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

def generate_synthetic_data(n_samples=2000):
    """
    Membuat data latih sintetis. 
    Kita menanamkan 'pola' agar AI bisa belajar, bukan sekadar acak.
    """
    print("🔄 Generating synthetic agriculture data...")
    
    data = []
    # Daftar ID Wilayah (Kita pakai dummy ID acak)
    regions = [f"{random.randint(11, 94)}{random.randint(10, 99)}" for _ in range(50)]
    
    for _ in range(n_samples):
        region_id = random.choice(regions)
        
        # Fitur: Curah Hujan (mm/bulan)
        rainfall = random.uniform(0, 400)
        
        # Fitur: NDVI (Indeks Hijau Daun) - 0.0 s/d 1.0
        ndvi = random.uniform(0.1, 0.9)
        
        # Fitur: Luas Lahan (Hektar)
        land_area = random.randint(50, 1000)
        
        # Fitur: Harga Pupuk (Rupiah/kg)
        price = random.uniform(2000, 5000)
        
        # --- LOGIC BISNIS PERTANIAN (POLA) ---
        # Rumus ini yang akan "ditebak" oleh AI nantinya
        
        base_demand = land_area * 0.25 # Asumsi 250kg/ha
        
        # Faktor Hujan: Tanaman butuh air, tapi kalau banjir (300mm+) demand turun
        rain_factor = 1.0
        if 100 < rainfall < 300: rain_factor = 1.3 # Musim tanam optimal
        elif rainfall > 350: rain_factor = 0.5     # Banjir
        
        # Faktor NDVI: Kalau 0.3-0.6 berarti fase vegetatif (butuh Urea banyak)
        ndvi_factor = 1.0
        if 0.3 < ndvi < 0.6: ndvi_factor = 1.4
        
        # Faktor Harga: Kalau mahal, beli sedikit
        price_factor = 1.0
        if price > 4000: price_factor = 0.8
        
        # Hitung Demand Akhir (Target)
        final_demand = base_demand * rain_factor * ndvi_factor * price_factor
        
        # Tambah sedikit "noise" (ketidakpastian) agar lebih realistis
        final_demand += random.uniform(-10, 10)
        final_demand = max(0, int(final_demand))
        
        data.append([region_id, rainfall, ndvi, land_area, price, final_demand])
        
    return pd.DataFrame(data, columns=['region_id', 'rainfall', 'ndvi', 'land_area', 'price', 'demand'])

def train():
    # 1. Buat Data
    df = generate_synthetic_data()
    
    # 2. Pisahkan Fitur (X) dan Target (y)
    X = df.drop(columns=['demand'])
    y = df['demand']
    
    # 3. Definisikan Fitur Kategorikal (Penting buat CatBoost!)
    cat_features = ['region_id']
    
    # 4. Train Model
    print("🚀 Training CatBoost Model...")
    model = CatBoostRegressor(
        iterations=500,
        learning_rate=0.1,
        depth=6,
        loss_function='RMSE',
        verbose=100
    )
    
    model.fit(X, y, cat_features=cat_features)
    
    # 5. Simpan Model
    model.save_model(MODEL_PATH)
    print(f"✅ Model saved successfully at: {MODEL_PATH}")

if __name__ == "__main__":
    train()