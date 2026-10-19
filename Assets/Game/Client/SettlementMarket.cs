using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Warfare.Core;
using Warfare.Core.World;

namespace Warfare.Client
{
    public sealed class MarketCategory
    {
        public string id;
        public string name;
        public string nameEn;
        public string icon;
        public MarketCategory[] sub = Array.Empty<MarketCategory>();
    }

    public sealed class EquipmentSlot
    {
        public string id;
        public string name;
        public string nameEn;
        public string column;
        public string icon;
    }

    public sealed class EquipmentData
    {
        public EquipmentSlot[] slots = Array.Empty<EquipmentSlot>();
    }

    public sealed class GoodData
    {
        public string id;
        public string name;
        public string nameEn;
        public int price;
        public string icon;
    }

    public sealed class GoodsData
    {
        public GoodData[] goods = Array.Empty<GoodData>();
    }

    public sealed class MarketData
    {
        public bool testStock;
        public MarketCategory[] categories = Array.Empty<MarketCategory>();
        public Dictionary<string, string[]> settlements = new Dictionary<string, string[]>();
    }

    public sealed partial class SettlementScreen
    {
        MarketData marketData;
        bool market;
        string marketTitle, marketCat;
        EquipmentData equipment;
        HeroPreview preview;
        int heroIndex;
        readonly List<Good> goodList = new List<Good>();
        readonly Dictionary<string, string> goodIcons = new Dictionary<string, string>();
        readonly Dictionary<string, Stock> stocks = new Dictionary<string, Stock>();
        Vector2 leftScroll, rightScroll;
        string dealNote;
        Good selectedGood, tipGood;
        Stock savedInventory, savedStock;
        int savedGold, dealsMade;
        AudioSource sfx;
        AudioClip coinClip;
        bool sortDesc;
        string sortBy;
        bool selectedBuying, tipBuying;
        float amount = 1f;
        GUIStyle sliderTrack, sliderThumb;
        float dealNoteUntil;
        GUIStyle tabLabel, header, headerRight, emptyText, letter, slotLabel, slotItem;
        string tip;
        readonly Dictionary<string, Texture2D> icons = new Dictionary<string, Texture2D>();

        void LoadMarket()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "market.json");
            marketData = (File.Exists(path) ? DataJson.Read<MarketData>(File.ReadAllText(path)) : null) ?? new MarketData();
            path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "equipment.json");
            equipment = (File.Exists(path) ? DataJson.Read<EquipmentData>(File.ReadAllText(path)) : null) ?? new EquipmentData();
            path = Path.Combine(Application.streamingAssetsPath, "Data", "world", "goods.json");
            var goods = (File.Exists(path) ? DataJson.Read<GoodsData>(File.ReadAllText(path)) : null) ?? new GoodsData();
            goodList.Clear();
            goodIcons.Clear();
            foreach (var g in goods.goods)
            {
                goodList.Add(new Good { Id = g.id, Name = g.name, Price = g.price });
                if (!string.IsNullOrEmpty(g.icon)) goodIcons[g.id] = g.icon;
            }
        }

        List<MarketCategory> MarketCategories(PlacedSettlement s)
        {
            var list = new List<MarketCategory>();
            string kindId = s.Kind == SettlementKind.Town ? "town" : s.Kind == SettlementKind.Castle ? "castle" : "village";
            if (marketData?.settlements == null || !marketData.settlements.TryGetValue(kindId, out var ids)) return list;
            foreach (var id in ids)
                foreach (var c in marketData.categories)
                    if (c.id == id) list.Add(c);
            return list;
        }

        void OpenMarket(string titleText)
        {
            market = true;
            marketTitle = titleText;
            var cats = MarketCategories(Current);
            marketCat = cats.Count > 0 ? cats[0].id : null;
            CurrentStock();
            SaveDeal();
            if (preview == null) preview = HeroPreview.Create();
            var heroes = PartyHeroes();
            if (heroIndex >= heroes.Count) heroIndex = 0;
            ShowHero();
            preview.Show(true);
            Debug.Log($"[W1347] market at {Current.Data.id}: {cats.Count} categories");
        }

        Texture2D Icon(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            if (!icons.TryGetValue(id, out var t)) icons[id] = t = Load(Path.Combine(uiDir, "icons"), id);
            return t;
        }

        void MarketSetup()
        {
            tabLabel = new GUIStyle(kind) { alignment = TextAnchor.MiddleCenter };
            header = new GUIStyle(kind) { alignment = TextAnchor.MiddleLeft };
            headerRight = new GUIStyle(kind) { alignment = TextAnchor.MiddleRight };
            emptyText = new GUIStyle(about) { alignment = TextAnchor.MiddleCenter };
            letter = new GUIStyle(title) { alignment = TextAnchor.MiddleCenter };
            slotLabel = new GUIStyle(kind) { alignment = TextAnchor.LowerCenter, wordWrap = true };
            slotItem = new GUIStyle(kind) { alignment = TextAnchor.MiddleCenter, wordWrap = true };
            var edge = new Color(0.62f, 0.48f, 0.25f);
            var dark = new Color(0.05f, 0.035f, 0.025f);
            sliderTrack = new GUIStyle { border = new RectOffset(4, 4, 4, 4) };
            sliderTrack.normal.background = Plate(new Color(0.12f, 0.09f, 0.06f), new Color(0.08f, 0.06f, 0.04f), edge, dark);
            sliderThumb = new GUIStyle { border = new RectOffset(4, 4, 4, 4) };
            sliderThumb.normal.background = Plate(new Color(0.95f, 0.78f, 0.42f), new Color(0.66f, 0.5f, 0.24f), new Color(1f, 0.9f, 0.6f), dark);
            sliderThumb.hover.background = sliderThumb.active.background = sliderThumb.normal.background;
        }

        void Outline(Rect r, Color c, float t)
        {
            Line(new Rect(r.x, r.y, r.width, t), c);
            Line(new Rect(r.x, r.yMax - t, r.width, t), c);
            Line(new Rect(r.x, r.y, t, r.height), c);
            Line(new Rect(r.xMax - t, r.y, t, r.height), c);
        }

        void Pane(Rect r, string caption, string emptyLine, float k, Stock stock, bool marketSide, ref Vector2 scroll)
        {
            GUI.color = new Color(0f, 0f, 0f, 0.32f);
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            Outline(r, new Color(Gold.r, Gold.g, Gold.b, 0.55f), Mathf.Max(1f, 1f * k));
            float m = 14f * k, aw = 28f * k;
            Shadowed(new Rect(r.x + m, r.y + 8f * k, r.width - m * 2f, 24f * k), caption, header, new Color(1f, 0.86f, 0.5f), k);
            float hy = r.y + 40f * k;
            var dim = new Color(Ink.r, Ink.g, Ink.b, 0.6f);
            float left = m + (marketSide ? aw : 0f), right = r.width - m - (marketSide ? 0f : aw);
            float priceX = right - 80f * k, qtyX = priceX - 100f * k;
            SortHeader(new Rect(r.x + left, hy, 140f * k, 20f * k), "Название", "name", false, k);
            Shadowed(new Rect(r.x + qtyX, hy, 90f * k, 20f * k), "Кол-во", headerRight, dim, k);
            SortHeader(new Rect(r.x + priceX, hy, 80f * k, 20f * k), "Цена", "price", true, k);
            Line(new Rect(r.x + m, hy + 24f * k, r.width - m * 2f, Mathf.Max(1f, 1f * k)), new Color(Gold.r, Gold.g, Gold.b, 0.45f));

            var rows = new List<Good>();
            if (stock != null && marketCat == "goods")
                foreach (var g in goodList)
                    if (stock.Count(g.Id) > 0) rows.Add(g);
            SortRows(rows);
            if (rows.Count == 0)
            {
                Shadowed(new Rect(r.x + m, r.y + r.height * 0.42f, r.width - m * 2f, 60f * k), emptyLine, emptyText, new Color(Ink.r, Ink.g, Ink.b, 0.7f), k);
                return;
            }

            float rowH = 34f * k;
            var view = new Rect(r.x, hy + 30f * k, r.width, r.yMax - hy - 36f * k);
            var content = new Rect(0f, 0f, view.width, rows.Count * rowH);
            bool inView = view.Contains(Event.current.mousePosition);
            scroll = GUI.BeginScrollView(view, scroll, content, false, false, GUIStyle.none, GUIStyle.none);
            var e = Event.current;
            for (int i = 0; i < rows.Count; i++)
            {
                var g = rows[i];
                var row = new Rect(4f * k, i * rowH, view.width - 8f * k, rowH);
                var arrow = marketSide ? new Rect(m - 6f * k, row.y + 4f * k, aw - 4f * k, rowH - 8f * k) : new Rect(right + 6f * k, row.y + 4f * k, aw - 4f * k, rowH - 8f * k);
                bool picked = selectedGood == g && selectedBuying == marketSide;
                bool hover = inView && row.Contains(e.mousePosition);
                bool overArrow = inView && arrow.Contains(e.mousePosition);
                if (picked || hover)
                {
                    GUI.color = new Color(0.96f, 0.76f, 0.3f, picked ? 0.24f : 0.13f);
                    GUI.DrawTexture(row, Texture2D.whiteTexture);
                }
                if (hover && !overArrow && !Dealing)
                {
                    tipGood = g;
                    tipBuying = marketSide;
                }
                if (overArrow) tip = marketSide ? "Купить всё" : "Продать всё";
                GUI.color = new Color(0f, 0f, 0f, overArrow ? 0.55f : 0.35f);
                GUI.DrawTexture(arrow, Texture2D.whiteTexture);
                Outline(arrow, new Color(Gold.r, Gold.g, Gold.b, overArrow ? 1f : 0.6f), Mathf.Max(1f, 1f * k));
                Shadowed(new Rect(arrow.x, arrow.y - 3f * k, arrow.width, arrow.height), marketSide ? "‹" : "›", letter, new Color(1f, 0.86f, 0.5f, overArrow ? 1f : 0.8f), k);
                float isz = rowH - 6f * k;
                if (goodIcons.TryGetValue(g.Id, out var iconId))
                {
                    var tex = Icon(iconId);
                    if (tex != null)
                    {
                        GUI.color = Color.white;
                        GUI.DrawTexture(new Rect(left - 2f * k, row.y + 3f * k, isz, isz), tex, ScaleMode.ScaleToFit);
                    }
                }
                float lx = left - 2f * k + isz + 8f * k;
                Shadowed(new Rect(lx, row.y, qtyX - lx, rowH), g.Name, header, Ink, k);
                Shadowed(new Rect(qtyX, row.y, 90f * k, rowH), stock.Count(g.Id).ToString(), headerRight, Ink, k);
                int price = marketSide ? Trade.BuyPrice(g) : Trade.SellPrice(g);
                Shadowed(new Rect(priceX, row.y, 80f * k, rowH), price.ToString(), headerRight, new Color(1f, 0.86f, 0.5f), k);
                GUI.color = Color.white;
                if (inView && Click(arrow)) Deal(g, marketSide, int.MaxValue);
                else if (inView && Click(row)) Pick(g, marketSide);
            }
            GUI.EndScrollView();
        }

        void Pick(Good g, bool buying)
        {
            selectedGood = g;
            selectedBuying = buying;
            amount = 1f;
        }

        int MaxDeal(Good g, bool buying)
        {
            var stock = CurrentStock();
            if (g == null || stock == null || Owner == null || Owner.Hero == null) return 0;
            if (!buying) return Owner.Inventory.Count(g.Id);
            return Mathf.Min(stock.Count(g.Id), Owner.Hero.Gold / Trade.BuyPrice(g));
        }

        void ItemTip(float k, Vector2 mouse)
        {
            var g = tipGood;
            if (g == null) return;
            var stock = CurrentStock();
            int have = Owner != null ? Owner.Inventory.Count(g.Id) : 0, there = stock != null ? stock.Count(g.Id) : 0;
            float w = 250f * k, h = 150f * k;
            var r = new Rect(mouse.x + 18f * k, mouse.y + 14f * k, w, h);
            if (r.xMax > Screen.width) r.x = mouse.x - w - 12f * k;
            if (r.yMax > Screen.height) r.y = Screen.height - h - 4f * k;
            GUI.color = new Color(0.06f, 0.045f, 0.035f, 0.96f);
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            Outline(r, Gold, Mathf.Max(1f, 1.2f * k));
            Shadowed(new Rect(r.x, r.y + 8f * k, w, 26f * k), g.Name, title, new Color(1f, 0.86f, 0.5f), k);
            float isz = 56f * k;
            if (goodIcons.TryGetValue(g.Id, out var iconId) && Icon(iconId) != null)
            {
                GUI.color = Color.white;
                GUI.DrawTexture(new Rect(r.center.x - isz / 2f, r.y + 38f * k, isz, isz), Icon(iconId), ScaleMode.ScaleToFit);
            }
            float ty = r.y + 100f * k;
            string offer = tipBuying ? $"Купить за {Trade.BuyPrice(g)}" : $"Продать за {Trade.SellPrice(g)}";
            Shadowed(new Rect(r.x, ty, w, 20f * k), offer, tabLabel, Ink, k);
            Shadowed(new Rect(r.x, ty + 22f * k, w, 20f * k), $"У вас {have}, на прилавке {there}", tabLabel, new Color(Ink.r, Ink.g, Ink.b, 0.75f), k);
        }

        bool Dealing => selectedGood != null;

        bool Click(Rect r) => !Dealing && GUI.Button(r, GUIContent.none, GUIStyle.none);

        void SortHeader(Rect r, string text, string key, bool rightAligned, float k)
        {
            bool on = sortBy == key;
            var ink = on ? new Color(1f, 0.86f, 0.5f) : new Color(Ink.r, Ink.g, Ink.b, r.Contains(Event.current.mousePosition) ? 0.95f : 0.6f);
            var style = rightAligned ? headerRight : header;
            Shadowed(r, text, style, ink, k);
            if (on)
            {
                float tw = style.CalcSize(new GUIContent(text)).x;
                float ax = rightAligned ? r.xMax - tw - 16f * k : r.x + tw + 4f * k;
                var ar = new Rect(ax, r.y - 2f * k, 14f * k, r.height + 4f * k);
                var keep = GUI.matrix;
                GUIUtility.RotateAroundPivot(sortDesc ? -90f : 90f, ar.center);
                Shadowed(ar, "‹", header, ink, k);
                GUI.matrix = keep;
            }
            GUI.color = Color.white;
            if (Click(r))
            {
                if (sortBy == key) sortDesc = !sortDesc;
                else
                {
                    sortBy = key;
                    sortDesc = false;
                }
            }
        }

        void SortRows(List<Good> rows)
        {
            if (sortBy == "name") rows.Sort((a, b) => string.Compare(a.Name, b.Name, StringComparison.CurrentCulture));
            else if (sortBy == "price") rows.Sort((a, b) => a.Price.CompareTo(b.Price));
            else return;
            if (sortDesc) rows.Reverse();
        }

        void SaveDeal()
        {
            var stock = CurrentStock();
            savedInventory = Owner != null ? Owner.Inventory.Clone() : new Stock();
            savedStock = stock != null ? stock.Clone() : new Stock();
            savedGold = Owner != null && Owner.Hero != null ? Owner.Hero.Gold : 0;
            dealsMade = 0;
        }

        void ResetDeal()
        {
            if (Owner == null || Owner.Hero == null || savedInventory == null) return;
            Owner.Inventory.CopyFrom(savedInventory);
            CurrentStock()?.CopyFrom(savedStock);
            Owner.Hero.Gold = savedGold;
            selectedGood = null;
            dealsMade = 0;
        }

        void PlayCoins()
        {
            if (coinClip == null) coinClip = Resources.Load<AudioClip>("Audio/coins");
            if (coinClip == null) return;
            if (sfx == null)
            {
                sfx = gameObject.AddComponent<AudioSource>();
                sfx.playOnAwake = false;
                sfx.spatialBlend = 0f;
            }
            sfx.PlayOneShot(coinClip, 0.8f);
        }

        void CancelMarket()
        {
            ResetDeal();
            CloseMarket();
        }

        void ResetButton(Rect r, float k, Vector2 mouse)
        {
            bool hover = r.Contains(mouse) && !Dealing;
            var tex = Icon("icon_reset");
            GUI.color = Color.white;
            if (tex != null)
            {
                GUI.color = new Color(1f, 1f, 1f, hover ? 1f : 0.85f);
                GUI.DrawTexture(r, tex, ScaleMode.ScaleToFit);
            }
            else
            {
                GUI.color = new Color(0f, 0f, 0f, 0.45f);
                GUI.DrawTexture(r, Texture2D.whiteTexture);
                Outline(r, new Color(Gold.r, Gold.g, Gold.b, hover ? 1f : 0.6f), Mathf.Max(1f, 1.2f * k));
                Shadowed(r, "Сброс", slotItem, new Color(1f, 0.86f, 0.5f), k);
            }
            if (hover) tip = "Сброс: вернуть всё, как было до сделок";
            GUI.color = Color.white;
            if (Click(r)) ResetDeal();
        }

        void DealWindow(Rect win, float k, Vector2 mouse)
        {
            var g = selectedGood;
            var e = Event.current;
            GUI.color = new Color(0f, 0f, 0f, 0.5f);
            GUI.DrawTexture(new Rect(0f, 0f, Screen.width, Screen.height), Texture2D.whiteTexture);
            float w = 470f * k, h = 340f * k;
            var r = new Rect(win.center.x - w / 2f, win.center.y - h / 2f, w, h);
            GUI.color = Color.white;
            if (panelStyle != null) GUI.Box(r, GUIContent.none, panelStyle);
            else GUI.DrawTexture(r, panelTex);
            if (e.type == EventType.MouseDown && !r.Contains(mouse))
            {
                selectedGood = null;
                e.Use();
                return;
            }
            Shadowed(new Rect(r.x, r.y + 26f * k, w, 30f * k), g.Name, title, new Color(1f, 0.86f, 0.5f), k);
            float isz = 72f * k;
            if (goodIcons.TryGetValue(g.Id, out var iconId) && Icon(iconId) != null)
            {
                GUI.color = Color.white;
                GUI.DrawTexture(new Rect(r.center.x - isz / 2f, r.y + 62f * k, isz, isz), Icon(iconId), ScaleMode.ScaleToFit);
            }
            var stock = CurrentStock();
            int have = Owner != null ? Owner.Inventory.Count(g.Id) : 0, there = stock != null ? stock.Count(g.Id) : 0;
            int price = selectedBuying ? Trade.BuyPrice(g) : Trade.SellPrice(g);
            float ty = r.y + 142f * k;
            Shadowed(new Rect(r.x, ty, w, 22f * k), selectedBuying ? $"Купить за {price}" : $"Продать за {price}", tabLabel, Ink, k);
            Shadowed(new Rect(r.x, ty + 22f * k, w, 22f * k), $"У вас {have}, на прилавке {there}", tabLabel, new Color(Ink.r, Ink.g, Ink.b, 0.75f), k);

            int max = MaxDeal(g, selectedBuying);
            int n = Mathf.Clamp(Mathf.RoundToInt(amount), max > 0 ? 1 : 0, Mathf.Max(0, max));
            var track = new Rect(r.x + w * 0.14f, ty + 60f * k, w * 0.72f, 12f * k);
            if (max > 1)
            {
                sliderTrack.fixedHeight = track.height;
                sliderThumb.fixedWidth = 14f * k;
                sliderThumb.fixedHeight = 26f * k;
                sliderThumb.margin = new RectOffset(0, 0, Mathf.RoundToInt(-7f * k), 0);
                GUI.color = Color.white;
                amount = GUI.HorizontalSlider(track, Mathf.Clamp(amount, 1f, max), 1f, max, sliderTrack, sliderThumb);
                n = Mathf.Clamp(Mathf.RoundToInt(amount), 1, max);
            }
            string what = max == 0 ? (selectedBuying ? "Не хватает золота" : "Нечего продать") : $"{n} шт. за {n * price}";
            Shadowed(new Rect(r.x, ty + 82f * k, w, 26f * k), what, header == null ? title : tabLabel, max == 0 ? new Color(1f, 0.55f, 0.45f) : new Color(1f, 0.86f, 0.5f), k);

            float bw = 170f * k, bh = 42f * k, gap = 18f * k, by = r.yMax - 34f * k - bh;
            GUI.color = Color.white;
            if (GUI.Button(new Rect(r.center.x - gap / 2f - bw, by, bw, bh), "Закрыть", button)) selectedGood = null;
            GUI.enabled = max > 0;
            if (GUI.Button(new Rect(r.center.x + gap / 2f, by, bw, bh), selectedBuying ? "Купить" : "Продать", button) && max > 0)
            {
                Deal(g, selectedBuying, n);
                amount = 1f;
                if (MaxDeal(g, selectedBuying) == 0) selectedGood = null;
            }
            GUI.enabled = true;
        }

        void Deal(Good g, bool buying, int want)
        {
            var stock = CurrentStock();
            if (Owner == null || Owner.Hero == null || stock == null) return;
            int gold = Owner.Hero.Gold;
            int done = buying ? Trade.Buy(g, stock, Owner.Inventory, ref gold, want) : Trade.Sell(g, stock, Owner.Inventory, ref gold, want);
            if (done > 0) dealsMade++;
            Owner.Hero.Gold = gold;
            if (buying && done == 0 && stock.Count(g.Id) > 0) Note("Не хватает золота");
        }

        void Note(string text)
        {
            dealNote = text;
            dealNoteUntil = Time.unscaledTime + 2.5f;
        }

        Stock CurrentStock()
        {
            if (Current == null) return null;
            if (!stocks.TryGetValue(Current.Data.id, out var stock))
            {
                stock = new Stock();
                if (marketData != null && marketData.testStock) FillTestStock(stock, Current);
                stocks[Current.Data.id] = stock;
            }
            return stock;
        }

        void FillTestStock(Stock stock, PlacedSettlement s)
        {
            var rng = new System.Random(s.Data.id.GetHashCode());
            bool village = s.Kind == SettlementKind.Village;
            foreach (var g in goodList)
            {
                if (village && rng.NextDouble() > 0.35) continue;
                stock.Add(g.Id, village ? rng.Next(3, 21) : rng.Next(5, 41));
            }
        }

        void CloseMarket()
        {
            market = false;
            selectedGood = null;
            if (preview != null) preview.Show(false);
        }

        List<HeroFile> PartyHeroes() => Owner != null ? Owner.Heroes : new List<HeroFile>();

        HeroFile SelectedHero()
        {
            var heroes = PartyHeroes();
            return heroes.Count > 0 ? heroes[Mathf.Clamp(heroIndex, 0, heroes.Count - 1)] : null;
        }

        void ShowHero()
        {
            if (preview == null || Owner == null) return;
            preview.SetFigure(Owner.BuildFigure(SelectedHero()));
        }

        void StepHero(int dir)
        {
            int n = PartyHeroes().Count;
            if (n < 2) return;
            heroIndex = (heroIndex + dir + n) % n;
            ShowHero();
        }

        string Equipped(string slotId)
        {
            var eq = SelectedHero()?.Equipment;
            return eq != null && eq.TryGetValue(slotId, out var item) && !string.IsNullOrEmpty(item) ? item : null;
        }

        void Slot(Rect r, EquipmentSlot slot, float k, Vector2 mouse)
        {
            bool hover = r.Contains(mouse);
            string item = Equipped(slot.id);
            GUI.color = new Color(0f, 0f, 0f, 0.45f);
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            Outline(r, new Color(Gold.r, Gold.g, Gold.b, hover || item != null ? 0.95f : 0.5f), Mathf.Max(1f, (hover ? 1.6f : 1f) * k));
            var tex = Icon(slot.icon);
            float isz = Mathf.Min(r.width, r.height) * 0.72f;
            var ir = new Rect(r.center.x - isz / 2f, r.center.y - isz / 2f, isz, isz);
            if (item != null) Shadowed(new Rect(r.x + 3f * k, r.y + 2f * k, r.width - 6f * k, r.height - 4f * k), item, slotItem, Ink, k);
            else if (tex != null)
            {
                GUI.color = new Color(1f, 1f, 1f, 0.5f);
                GUI.DrawTexture(ir, tex, ScaleMode.ScaleToFit);
            }
            if (hover) tip = item != null ? $"{slot.name}: {item}" : slot.name;
        }

        void Tip(float k, Vector2 mouse)
        {
            if (string.IsNullOrEmpty(tip)) return;
            var size = slotLabel.CalcSize(new GUIContent(tip));
            var r = new Rect(mouse.x + 16f * k, mouse.y + 18f * k, size.x + 20f * k, size.y + 10f * k);
            if (r.xMax > Screen.width) r.x = mouse.x - r.width - 8f * k;
            GUI.color = new Color(0.06f, 0.045f, 0.035f, 0.95f);
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            Outline(r, Gold, Mathf.Max(1f, 1f * k));
            Shadowed(r, tip, slotItem, Ink, k);
        }

        void DrawMarket(PlacedSettlement s, float k)
        {
            if (tabLabel == null) MarketSetup();
            var prev = GUI.color;
            tabLabel.fontSize = header.fontSize = headerRight.fontSize = Mathf.RoundToInt(13.5f * k);
            emptyText.fontSize = Mathf.RoundToInt(14 * k);
            letter.fontSize = Mathf.RoundToInt(24 * k);
            slotLabel.fontSize = slotItem.fontSize = Mathf.RoundToInt(11.5f * k);
            var e = Event.current;
            var mouse = e.mousePosition;
            tip = null;
            tipGood = null;

            var win = new Rect(Screen.width * 0.04f, Screen.height * 0.05f, Screen.width * 0.92f, Screen.height * 0.9f);
            GUI.color = Color.white;
            if (panelStyle != null) GUI.Box(win, GUIContent.none, panelStyle);
            else GUI.DrawTexture(win, panelTex);

            float bw = Mathf.Min(win.width * 0.36f, 520f * k), bh = 44f * k;
            var band = new Rect(win.center.x - bw / 2f, win.y + 24f * k, bw, bh);
            GUI.color = Color.white;
            if (ribbonStyle != null) GUI.Box(new Rect(band.x - bw * 0.06f, band.y - 4f * k, bw * 1.12f, bh + 8f * k), GUIContent.none, ribbonStyle);
            Shadowed(new Rect(band.x, band.y + 3f * k, band.width, band.height - 6f * k), (marketTitle ?? "").ToUpperInvariant(), title, Ink, k);
            Shadowed(new Rect(win.x, band.yMax + 4f * k, win.width, 20f * k), $"{s.Data.name}, {KindName(s).ToLowerInvariant()}", tabLabel, kind.normal.textColor, k);

            var cats = MarketCategories(s);
            float tw = 112f * k, th = 84f * k, gap = 14f * k;
            float tx = win.center.x - (cats.Count * tw + Mathf.Max(0, cats.Count - 1) * gap) / 2f, ty = band.yMax + 30f * k;
            foreach (var c in cats)
            {
                var r = new Rect(tx, ty, tw, th);
                bool on = c.id == marketCat, hover = r.Contains(mouse);
                float isz = 52f * k;
                var ir = new Rect(r.center.x - isz / 2f, r.y, isz, isz);
                var tex = Icon(c.icon);
                float a = on || hover ? 1f : 0.62f;
                if (tex != null)
                {
                    GUI.color = new Color(1f, 1f, 1f, a);
                    GUI.DrawTexture(ir, tex, ScaleMode.ScaleToFit);
                }
                else
                {
                    Outline(ir, new Color(Gold.r, Gold.g, Gold.b, a), Mathf.Max(1f, 1.5f * k));
                    Shadowed(ir, c.name.Substring(0, 1), letter, new Color(1f, 0.86f, 0.5f, a), k);
                }
                var ink = on ? new Color(1f, 0.86f, 0.5f) : hover ? Ink : new Color(Ink.r, Ink.g, Ink.b, 0.7f);
                Shadowed(new Rect(r.x - 12f * k, ir.yMax + 4f * k, r.width + 24f * k, 20f * k), c.name, tabLabel, ink, k);
                if (on) Line(new Rect(r.x + r.width * 0.18f, r.yMax - 3f * k, r.width * 0.64f, Mathf.Max(1f, 2f * k)), Gold);
                GUI.color = Color.white;
                if (Click(r))
                {
                    marketCat = c.id;
                    selectedGood = null;
                }
                tx += tw + gap;
            }

            float cy = ty + th + 10f * k;
            if (divider != null)
            {
                float dw = win.width * 0.4f, dh = dw * divider.height / divider.width;
                GUI.color = Color.white;
                GUI.DrawTexture(new Rect(win.center.x - dw / 2f, cy - dh / 2f, dw, dh), divider);
            }
            cy += 14f * k;

            float pad = 30f * k, barH = 44f * k;
            float bottom = win.yMax - 30f * k - barH - 14f * k;
            float midW = win.width * 0.34f;
            float pw = (win.width - midW - pad * 4f) / 2f;
            var left = new Rect(win.x + pad, cy, pw, bottom - cy);
            var mid = new Rect(left.xMax + pad, cy, midW, bottom - cy);
            var right = new Rect(mid.xMax + pad, cy, pw, bottom - cy);
            Pane(left, "У вас", "Ваши сумы пусты.", k, Owner != null ? Owner.Inventory : null, false, ref leftScroll);
            Pane(right, s.Kind == SettlementKind.Village ? "У крестьян" : "На рынке", s.Kind == SettlementKind.Village ? "Крестьянам пока нечего продать." : "Прилавки пока пусты.", k, CurrentStock(), true, ref rightScroll);

            var heroes = PartyHeroes();
            string heroName = SelectedHero()?.Name ?? "Герой";
            var nameSize = title.CalcSize(new GUIContent(heroName));
            Shadowed(new Rect(mid.x, mid.y - 4f * k, mid.width, 30f * k), heroName, title, new Color(1f, 0.86f, 0.5f), k);
            bool many = heroes.Count > 1;
            float aw = 34f * k, ax = nameSize.x / 2f + 18f * k;
            var prevRect = new Rect(mid.center.x - ax - aw, mid.y - 4f * k, aw, 30f * k);
            var nextRect = new Rect(mid.center.x + ax, mid.y - 4f * k, aw, 30f * k);
            var arrowInk = new Color(1f, 0.86f, 0.5f, many ? (prevRect.Contains(mouse) || nextRect.Contains(mouse) ? 1f : 0.8f) : 0.25f);
            Shadowed(prevRect, "‹", letter, arrowInk, k);
            Shadowed(nextRect, "›", letter, arrowInk, k);
            GUI.color = Color.white;
            if (Click(prevRect)) StepHero(-1);
            if (Click(nextRect)) StepHero(1);
            float sg = 10f * k, top = mid.y + 30f * k;
            var slots = equipment?.slots ?? Array.Empty<EquipmentSlot>();
            float slot = Mathf.Min(84f * k, (mid.yMax - top - sg * 4f) / 5f);
            float lx = mid.x, rx = mid.xMax - slot, sy = top, ry = top;
            float bottomY = top + (slot + sg) * 4f;
            var bottomSlots = new List<EquipmentSlot>();
            foreach (var sl in slots)
            {
                if (sl.column == "left")
                {
                    Slot(new Rect(lx, sy, slot, slot), sl, k, mouse);
                    sy += slot + sg;
                }
                else if (sl.column == "right")
                {
                    Slot(new Rect(rx, ry, slot, slot), sl, k, mouse);
                    ry += slot + sg;
                }
                else bottomSlots.Add(sl);
            }
            float bwide = slot * 1.7f;
            float bx = mid.center.x - (bottomSlots.Count * bwide + Mathf.Max(0, bottomSlots.Count - 1) * sg) / 2f;
            foreach (var sl in bottomSlots)
            {
                Slot(new Rect(bx, bottomY, bwide, slot), sl, k, mouse);
                bx += bwide + sg;
            }

            var fig = new Rect(lx + slot + sg, top, rx - lx - slot - sg * 2f, bottomY - top - sg);
            if (preview != null && preview.Texture != null)
            {
                GUI.color = Color.white;
                GUI.DrawTexture(fig, preview.Texture, ScaleMode.ScaleToFit, true);
                if (e.type == EventType.MouseDrag && fig.Contains(mouse) && !Dealing)
                {
                    preview.Spin(e.delta.x);
                    e.Use();
                }
                else if (e.type == EventType.ScrollWheel && fig.Contains(mouse) && !Dealing)
                {
                    preview.Spin(e.delta.y * 6f);
                    e.Use();
                }
            }

            float by = win.yMax - 30f * k - barH;
            var coin = Icon("icon_gold");
            float gx = win.x + pad;
            if (coin != null)
            {
                GUI.color = Color.white;
                GUI.DrawTexture(new Rect(gx, by + 4f * k, barH - 8f * k, barH - 8f * k), coin, ScaleMode.ScaleToFit);
                gx += barH;
            }
            int gold = Owner != null && Owner.Hero != null ? Owner.Hero.Gold : 0;
            var goldInk = new Color(1f, 0.86f, 0.5f);
            var goldSize = header.CalcSize(new GUIContent($"Золото: {gold}"));
            Shadowed(new Rect(gx, by, 300f * k, barH), $"Золото: {gold}", header, goldInk, k);
            int balance = gold - savedGold;
            if (balance != 0)
                Shadowed(new Rect(gx + goldSize.x + 16f * k, by, 260f * k, barH), balance > 0 ? $"за сделку +{balance}" : $"за сделку −{-balance}", header, balance > 0 ? new Color(0.62f, 0.9f, 0.5f) : new Color(1f, 0.55f, 0.45f), k);
            if (!string.IsNullOrEmpty(dealNote) && Time.unscaledTime < dealNoteUntil)
                Shadowed(new Rect(gx, by - 26f * k, 400f * k, 24f * k), dealNote, header, new Color(1f, 0.55f, 0.45f), k);
            float bw2 = 190f * k, rs = barH + 10f * k;
            var doneRect = new Rect(win.xMax - pad - bw2, by, bw2, barH);
            var resetRect = new Rect(doneRect.x - 14f * k - rs, by - 5f * k, rs, rs);
            var cancelRect = new Rect(resetRect.x - 14f * k - bw2, by, bw2, barH);
            GUI.color = Color.white;
            GUI.enabled = !Dealing;
            if (GUI.Button(cancelRect, "Отмена", button)) CancelMarket();
            ResetButton(resetRect, k, mouse);
            if (GUI.Button(doneRect, "Готово", button))
            {
                if (dealsMade > 0) PlayCoins();
                CloseMarket();
            }
            GUI.enabled = true;
            if (Dealing) DealWindow(win, k, mouse);
            ItemTip(k, mouse);
            Tip(k, mouse);
            GUI.color = prev;
        }
    }
}
