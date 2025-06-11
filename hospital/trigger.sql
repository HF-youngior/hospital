-- 触发器：在 MedicationDetail 插入后生成 Payment 记录
CREATE TRIGGER generate_payment_after_insert_medication
ON medication_detail
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    -- 插入 Payment 记录，基于所有插入的 MedicationDetail
    INSERT INTO payment (
        registration_id,
        fee_type,
        insurance_amount,
        self_pay_amount,
        pay_method,
        pay_time,
        pay_status
    )
    SELECT
        i.registration_id,
        N'药品费',
        SUM(d.price * d.insurance_rate) AS insurance_amount,
        SUM(d.price * (1 - d.insurance_rate)) AS self_pay_amount,
        N'微信支付',
        GETDATE(),
        N'未支付'
    FROM inserted i
    JOIN drug d ON i.drug_id = d.drug_id
    GROUP BY i.registration_id;
END;
GO

-- 触发器：在 CheckDetail 插入后生成 Payment 记录
CREATE TRIGGER generate_payment_after_insert_check
ON check_detail
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO payment (
        registration_id,
        fee_type,
        insurance_amount,
        self_pay_amount,
        pay_method,
        pay_time,
        pay_status
    )
    SELECT
        i.registration_id,
        N'检查费',
        SUM(ci.price * ci.insurance_rate) AS insurance_amount,
        SUM(ci.price * (1 - ci.insurance_rate)) AS self_pay_amount,
        N'微信支付',
        GETDATE(),
        N'未支付'
    FROM inserted i
    JOIN check_item ci ON i.item_id = ci.item_id
    GROUP BY i.registration_id;
END;
GO