SELECT
    "products".*,
    "manufacturers"."name" AS "manufacturer"
FROM
    "products"
    LEFT JOIN "manufacturers" ON "products"."manufacturer_id" = "manufacturers"."id";