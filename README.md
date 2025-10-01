# README – Projet ETL et Ingestion Snowflake  
**Groupe 2 – Emilie Boulanger, Maria Boussa, Hugo Braun,Jean-Baptiste Brun**

## Sommaire
1. [Contexte du projet](#contexte-du-projet)  
2. [Environnement](#environnement)  
3. [Structure des données](#structure-des-données)  
4. [Architecture du pipeline](#architecture-du-pipeline)  
5. [Méthodes d’ingestion](#méthodes-dingestion)  
   - 5.1 Insertion directe (INSERT)  
   - 5.2 Insertion par lot (Batch Insert)  
   - 5.3 COPY INTO (via stage)  
   - 5.4 Snowpipe (serverless et automatisé)  
6. [Monitoring et validation](#monitoring-et-validation)  
7. [Qualité des données](#qualité-des-données)  
8. [Troubleshooting](#troubleshooting)  
9. [Conclusion](#conclusion)  

-------------------------------------------------------------------------------

## 1. Contexte du projet
L’objectif du projet est de construire un pipeline d’ingestion de données dans Snowflake pour l’entreprise fictive **Maison Albert** (secteur parfums et cosmétiques).  

Les données sources sont générées aléatoirement à l’aide d’un script Python (`data_generator.py`). Elles sont ensuite chargées dans Snowflake en utilisant plusieurs approches afin de comparer leurs performances et leur pertinence dans un contexte réel.  

---------------------------------------------------------------------------

## 2. Environnement
- Gestion d’environnement : Miniconda  
- Environnement virtuel : `ETL_venv`  
- Version Python : **3.9**  
- Dépendances principales :  
  - `pandas`  
  - `pyarrow`  
  - `snowflake-connector-python`  
  - `snowflake-ingest`  
  - `python-dotenv`  
  - `faker`, `optional-faker`  

Authentification Snowflake : RSA key pair avec les variables d’environnement suivantes définies dans un fichier `.env` :  
```env
SNOWFLAKE_ACCOUNT=...
SNOWFLAKE_USER=...
PRIVATE_KEY=...
```
-------------------------------------------------------------------------------------------------------
Ressources Snowflake créees :  
- **Role** : `INGEST`  
- **Warehouse** : `INGEST`  
- **Database** : `INGEST`  
- **Schema** : `INGEST`  
- **Table cible** : `CLIENT_SUPPORT_ORDERS`  
- **Pipe (Snowpipe)** : `CLIENT_SUPPORT_ORDERS_PIPE`  

------------------------------------------------------------------------------------------------------

## 3. Structure des données
Les donnés générér décrivent des commandes clients.  

| Colonne             | Type            | Description |
|---------------------|-----------------|-------------|
| TXID                | STRING          | Identifiant unique de transaction |
| NAME                | STRING          | Nom du client |
| EMAIL               | STRING          | Adresse e-mail du client |
| ITEM                | STRING          | Nom du produit commandé |
| SIZE                | STRING          | Taille du produit |
| CATEGORY            | STRING          | Catégorie principale (parfum, maquillage, etc.) |
| SUB_CATEGORY        | STRING          | Sous-catégorie |
| GENDER              | STRING          | Genre associé au produit |
| PRICE               | DECIMAL(10,2)   | Prix du produit |
| PURCHASE_TIME       | TIMESTAMP       | Date et heure d’achat |
| DELIVERY_DATE       | DATE            | Date de livraison |
| DELIVERY_TIME       | NUMBER          | Durée de livraison (jours) |
| REFUNDED            | BOOLEAN         | Indique si la commande a été remboursée |
| REFUND_REASON       | STRING          | Motif du remboursement |
| REVIEW_SCORE        | NUMBER          | Note de l’avis (1 à 5) |
| REVIEW_TEXT         | STRING          | Commentaire laissé par le client |
| ADDRESS             | VARIANT (JSON)  | Adresse structurée du client |
| EMERGENCY_CONTACT   | VARIANT (JSON)  | Contact d’urgence (nom, téléphone, email) |

-----------------------------------------------------------------------------------

## 4. Architecture du pipeline
```
flowchart LR
  A[data_generator.py] --> B[INSERT / Batch Insert]
  A --> C[COPY INTO via stage]
  A --> D[Snowpipe]
  C -->|PUT parquet| E[@%CLIENT_SUPPORT_ORDERS stage]
  D --> E --> F[Table CLIENT_SUPPORT_ORDERS]
```

-------------------------------------------------------------------------------------

## 5. Méthodes d’ingestion

### 5.1 Insertion directe par INSERT
- Script : `py_insert.py`  
- Utilisation : lit les données générées et exécute des `INSERT` SQL ligne par ligne.  
- Avantage : simple.  
- Limite : devient long lorsqu'il y a bcp de lignes.  

### 5.2 Insertion par Batch Insert
- Script : version optimisée de `py_insert.py`.  
- Fonctionne en regroupant les lignes avant de les insérer.  
- Gain de performance significatif par rapport aux `INSERT` simples.  

### 5.3 COPY INTO via stage
- Script : `file_insert.py`  
- Étapes :  
  1. Génération de fichiers Parquet à partir des données.  
  2. `PUT` des fichiers dans un stage associé à la table.  
  3. Utilisation de `COPY INTO CLIENT_SUPPORT_ORDERS`.  
- Avantage : ingestion rapide et adaptée aux gros volumes.  
- Limite : nécessite un déclenchement manuel du `COPY INTO`.  

### 5.4 Snowpipe
- Script : `snowpipe.py`  
- Étapes :  
  1. Génération et `PUT` des fichiers dans le stage.  
  2. Déclenchement automatique du PIPE (`CLIENT_SUPPORT_ORDERS_PIPE`).  
  3. Insertion continue dans la table cible.  
- Avantage : ingestion quasi temps réel, automatisée, scalable.  
- Recommandation : méthode privilégiée pour la production.  

---------------------------------------------------------------------------------------------------------------------------------------

## 6. Monitoring et validation
on utilise ces requêtes SQL pour vérifier le fonctionnement du pipeline :  

- Compte le nombre total de lignes :
```
SELECT COUNT(*) FROM CLIENT_SUPPORT_ORDERS;
```

- Vérifier les dernières données ingérées :
```
SELECT * 
FROM CLIENT_SUPPORT_ORDERS
ORDER BY PURCHASE_TIME DESC
LIMIT 10;
```

- Suivre l’activité du Snowpipe :
```
SELECT *
FROM TABLE(INFORMATION_SCHEMA.PIPE_USAGE_HISTORY(
  PIPE_NAME => 'CLIENT_SUPPORT_ORDERS_PIPE'
));
```

- Vérifier les fichiers ingérés depuis le stage :
```
LIST @%CLIENT_SUPPORT_ORDERS;
```

- Statistiques d’achat :
```
SELECT DATE_TRUNC('hour', PURCHASE_TIME) AS heure, COUNT(*) AS nb_commandes
FROM CLIENT_SUPPORT_ORDERS
GROUP BY 1
ORDER BY 1;
```

- Produits les plus vendus :
```
SELECT ITEM, COUNT(*) AS ventes
FROM CLIENT_SUPPORT_ORDERS
GROUP BY ITEM
ORDER BY ventes DESC
LIMIT 5;
```

------------------------------------------------------------------------------------------------------------------------------------------

## 7. Qualité des données
on met en place des règles de validation pour nos analyses :  
- `PRICE >= 0`  
- `REVIEW_SCORE BETWEEN 1 AND 5`   
- Cohérence temporelle : `DELIVERY_DATE >= PURCHASE_TIME::DATE`  
- Colonnes obligatoires (`TXID`, `ITEM`, `PRICE`, `PURCHASE_TIME`) non nulles.  

----------------------------------------------------------------------------------

## 8. Troubleshooting
- on verifie l’existence et l’état des pipes :
```
SHOW PIPES;
```

- Pour relancer manuelement le pipe en cas d’erreur :
```
ALTER PIPE CLIENT_SUPPORT_ORDERS_PIPE REFRESH;
```

- check les logs d’ingestion Snowpipe :
```
SELECT * 
FROM TABLE(INFORMATION_SCHEMA.LOAD_HISTORY_BY_PIPE(
  PIPE_NAME => 'CLIENT_SUPPORT_ORDERS_PIPE'
))
ORDER BY LAST_LOAD_TIME DESC;
```

- check présence de fichiers restés non consommés dans le stage :
```sql
LIST @%CLIENT_SUPPORT_ORDERS;
```

----------------------------------------------------------------------------------

## 9. Conclusion
Nous avons exploré plusieurs méthodes d’ingestion dans Snowflake pour les données de Maison Albert :  
- `INSERT` : simple mais limité.  
- `Batch Insert` : amélioration notable sur les performances.  
- `COPY INTO` : ingestion en lot efficace, mais non automatisée.  
- `Snowpipe` : ingestion continue, automatisée.  

on retient **Snowpipe** comme solution, tout en présentant les autres approches comme alternatives pédagogiques.  
