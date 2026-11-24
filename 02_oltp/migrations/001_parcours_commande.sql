-- MenuScan TN - migration 001 : parcours de commande de l'application (décision D-24, validée le 24/11/2026)
-- Idempotente : peut être rejouée sans effet. Appliquée par 02_oltp/charger_base_app.py après le chargement, ou seule avec --migrer.
SET search_path TO menuscan;

-- 1. Étapes de la commande : nouvelle -> en_prepa -> prete -> servie (ou annulee), avec l'heure de chaque étape
ALTER TABLE commandes ADD COLUMN IF NOT EXISTS date_heure_acceptation TIMESTAMP;
ALTER TABLE commandes ADD COLUMN IF NOT EXISTS date_heure_prete TIMESTAMP;
UPDATE commandes SET statut_commande = 'nouvelle' WHERE statut_commande = 'en_cours';
ALTER TABLE commandes DROP CONSTRAINT IF EXISTS ck_commandes_statut;
ALTER TABLE commandes ADD CONSTRAINT ck_commandes_statut CHECK (statut_commande IN ('nouvelle', 'en_prepa', 'prete', 'servie', 'annulee'));

-- 2. Note du client pour le serveur
ALTER TABLE commandes ADD COLUMN IF NOT EXISTS note VARCHAR(200);

-- 3. Description des articles (une par nom d'article, rédigée pour l'application)
ALTER TABLE articles ADD COLUMN IF NOT EXISTS description VARCHAR(120);
UPDATE articles a SET description = d.description
FROM (VALUES
    ('Assida zgougou', 'Crème de pin d''Alep, garnie de fruits secs'),
    ('Baguette farcie', 'Pain croustillant, thon, harissa et crudités'),
    ('Baklawa', 'Feuilleté aux fruits secs et au miel'),
    ('Bambalouni', 'Beignet tunisien saupoudré de sucre'),
    ('Bouza', 'Crème de sorgho, servie fraîche'),
    ('Brik à l''oeuf', 'Feuille de malsouka croustillante, œuf et thon'),
    ('Brochettes de poulet', 'Poulet mariné grillé, frites et salade'),
    ('Burger classique', 'Steak haché, cheddar, salade et tomate'),
    ('Burger poulet', 'Poulet pané, salade et sauce maison'),
    ('Café crème', 'Express allongé au lait chaud'),
    ('Café glacé', 'Express servi sur glaçons'),
    ('Café turc', 'Café moulu fin, servi dans sa tasse traditionnelle'),
    ('Cake maison', 'Part de cake du jour'),
    ('Cappuccino', 'Express, lait chaud et mousse de lait'),
    ('Capucin', 'Express et nuage de lait, à la tunisienne'),
    ('Chapati', 'Galette garnie de thon, œuf et fromage'),
    ('Cheeseburger', 'Steak haché et double cheddar'),
    ('Cheesecake', 'Gâteau au fromage frais sur base biscuitée'),
    ('Chicha menthe', 'Parfum menthe'),
    ('Chicha pomme', 'Parfum pomme'),
    ('Chicha raisin', 'Parfum raisin'),
    ('Chocolat chaud', 'Lait chaud et cacao'),
    ('Chorba', 'Soupe tunisienne à l''agneau et aux plombs'),
    ('Citronnade', 'Citrons pressés et menthe fraîche'),
    ('Coupe glacée', 'Trois boules de glace et chantilly'),
    ('Couscous agneau', 'Semoule, agneau et légumes de saison'),
    ('Couscous poisson', 'Semoule, poisson et légumes de saison'),
    ('Croissant', 'Viennoiserie pur beurre'),
    ('Croissant aux amandes', 'Garni de crème d''amande'),
    ('Crème caramel', 'Flan aux œufs et caramel'),
    ('Crêpe Nutella', 'Crêpe garnie de pâte à tartiner'),
    ('Crêpe fromage', 'Crêpe salée au fromage fondu'),
    ('Côtelettes d''agneau', 'Côtelettes grillées, frites et salade'),
    ('Eau minérale 0,5 L', 'Bouteille de 50 cl'),
    ('Eau minérale 1 L', 'Bouteille d''un litre'),
    ('Escalope grillée', 'Escalope de poulet grillée, frites et salade'),
    ('Express', 'Café serré'),
    ('Fricassé', 'Petit pain frit au thon, œuf et harissa'),
    ('Frites', 'Portion de frites'),
    ('Frites fromage', 'Frites nappées de fromage fondu'),
    ('Fruits de saison', 'Assiette de fruits frais'),
    ('Gaufre chocolat', 'Gaufre chaude, sauce chocolat'),
    ('Infusion verveine', 'Verveine infusée'),
    ('Jus d''orange', 'Oranges pressées minute'),
    ('Jus de citron', 'Citrons pressés, sucre et eau fraîche'),
    ('Jus de fraise', 'Fraises mixées'),
    ('Kaak warka', 'Biscuit en couronne à la pâte d''amande'),
    ('Kafteji', 'Légumes frits hachés, œuf et piment'),
    ('Lablabi', 'Soupe de pois chiches, cumin et harissa'),
    ('Latte macchiato', 'Lait mousseux et express'),
    ('Libanais', 'Sandwich en pain libanais, garniture au choix'),
    ('Makroudh', 'Gâteau de semoule fourré aux dattes'),
    ('Merguez grillées', 'Merguez grillées, frites et salade'),
    ('Milk-shake', 'Lait, glace et fruits mixés'),
    ('Mille-feuille', 'Pâte feuilletée et crème pâtissière'),
    ('Mlawi thon', 'Galette feuilletée au thon et à la harissa'),
    ('Mloukhia', 'Ragoût de corète et de bœuf'),
    ('Mojito sans alcool', 'Citron vert, menthe et eau gazeuse'),
    ('Ojja fruits de mer', 'Sauce tomate épicée, œufs et fruits de mer'),
    ('Ojja merguez', 'Sauce tomate épicée, œufs et merguez'),
    ('Omelette', 'Omelette de trois œufs, servie avec du pain'),
    ('Pain au chocolat', 'Viennoiserie, deux barres de chocolat'),
    ('Pancakes', 'Pile de pancakes et nappage'),
    ('Penne au poulet', 'Pâtes au poulet et sauce crème'),
    ('Petit-déjeuner continental', 'Boisson chaude, jus, viennoiserie et tartines'),
    ('Petit-déjeuner tunisien', 'Boisson chaude, jus, bsissa, huile d''olive et pain'),
    ('Pizza 4 fromages', 'Base tomate et quatre fromages'),
    ('Pizza margherita', 'Tomate, mozzarella et origan'),
    ('Pizza thon', 'Tomate, mozzarella, thon et olives'),
    ('Poisson du jour', 'Poisson grillé, selon l''arrivage'),
    ('Salade méchouia', 'Poivrons et tomates grillés, thon et œuf'),
    ('Salade tunisienne', 'Tomate, concombre, oignon, thon et œuf'),
    ('Salade verte', 'Salade de saison'),
    ('Smoothie', 'Fruits mixés et yaourt'),
    ('Soda canette', 'Canette de 33 cl'),
    ('Sorbet citron', 'Deux boules de sorbet'),
    ('Spaghetti bolognaise', 'Sauce tomate et viande hachée'),
    ('Spaghetti fruits de mer', 'Sauce tomate et fruits de mer'),
    ('Tacos poulet', 'Galette garnie de poulet, frites et sauce fromagère'),
    ('Tacos viande hachée', 'Galette garnie de viande hachée, frites et sauce fromagère'),
    ('Tarte au citron', 'Tarte au citron meringuée'),
    ('Thé aux pignons', 'Thé à la menthe et pignons'),
    ('Thé glacé', 'Thé infusé, servi frais'),
    ('Thé rouge', 'Thé noir infusé'),
    ('Thé vert', 'Thé vert infusé'),
    ('Thé à la menthe', 'Thé vert à la menthe fraîche'),
    ('Tiramisu', 'Mascarpone, café et cacao')
) AS d(nom_article, description)
WHERE a.nom_article = d.nom_article AND a.description IS NULL;

-- 4. Ouverture ou fermeture des commandes par le gérant
ALTER TABLE etablissements ADD COLUMN IF NOT EXISTS commandes_ouvertes BOOLEAN NOT NULL DEFAULT TRUE;

-- Journal des migrations
CREATE TABLE IF NOT EXISTS migrations (migration_id VARCHAR(40) PRIMARY KEY, date_application TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
INSERT INTO migrations (migration_id) VALUES ('001_parcours_commande') ON CONFLICT DO NOTHING;
