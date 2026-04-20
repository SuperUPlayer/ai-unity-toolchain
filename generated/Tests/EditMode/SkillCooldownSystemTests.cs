// === Tests/EditMode/SkillCooldownSystemTests.cs
using NUnit.Framework;
using UnityEngine;
using Project.Skill;

public class SkillCooldownSystemTests
{
    private GameObject _gameObject;
    private SkillCooldownSystem _cooldownSystem;

    [SetUp]
    public void SetUp()
    {
        _gameObject = new GameObject();
        _cooldownSystem = _gameObject.AddComponent<SkillCooldownSystem>();
    }

    [TearDown]
    public void TearDown()
    {
        if (_gameObject != null)
        {
            Object.DestroyImmediate(_gameObject);
        }
    }

    #region 技能注册测试

    [Test]
    public void RegisterSkill_ValidSkill_AddsToDictionary()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f);

        _cooldownSystem.RegisterSkill(skillData);

        var retrieved = _cooldownSystem.GetSkillData(10001);
        Assert.IsNotNull(retrieved);
        Assert.AreEqual(10001, retrieved.SkillId);
        Assert.AreEqual("TestSkill", retrieved.SkillName);
    }

    [Test]
    public void RegisterSkill_NullSkill_DoesNotThrow()
    {
        Assert.DoesNotThrow(() => _cooldownSystem.RegisterSkill(null));
    }

    [Test]
    public void RegisterSkill_DuplicateSkillId_Overwrites()
    {
        var skill1 = CreateTestSkill(10001, "Skill1", 5f);
        var skill2 = CreateTestSkill(10001, "Skill2", 10f);

        _cooldownSystem.RegisterSkill(skill1);
        _cooldownSystem.RegisterSkill(skill2);

        var retrieved = _cooldownSystem.GetSkillData(10001);
        Assert.AreEqual("Skill2", retrieved.SkillName);
        Assert.AreEqual(10f, retrieved.Cooldown);
    }

    #endregion

    #region 冷却查询测试

    [Test]
    public void CanUseSkill_UnregisteredSkill_ReturnsFalse()
    {
        bool result = _cooldownSystem.CanUseSkill(99999);

        Assert.IsFalse(result);
    }

    [Test]
    public void CanUseSkill_RegisteredSkill_ReturnsTrue()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f);
        _cooldownSystem.RegisterSkill(skillData);

        bool result = _cooldownSystem.CanUseSkill(10001);

        Assert.IsTrue(result);
    }

    [Test]
    public void CanUseSkill_AfterTriggerCooldown_ReturnsFalse()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f);
        _cooldownSystem.RegisterSkill(skillData);
        _cooldownSystem.TriggerCooldown(10001);

        bool result = _cooldownSystem.CanUseSkill(10001);

        Assert.IsFalse(result);
    }

    [Test]
    public void CanUseSkill_SkillNotAffectedByGcd_IgnoresGcd()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f, false);
        _cooldownSystem.RegisterSkill(skillData);
        _cooldownSystem.TriggerGcd(1.0f);

        bool result = _cooldownSystem.CanUseSkill(10001);

        Assert.IsTrue(result);
    }

    #endregion

    #region 冷却触发测试

    [Test]
    public void TriggerCooldown_ValidSkill_ReturnsTrue()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f);
        _cooldownSystem.RegisterSkill(skillData);

        bool result = _cooldownSystem.TriggerCooldown(10001);

        Assert.IsTrue(result);
    }

    [Test]
    public void TriggerCooldown_UnregisteredSkill_ReturnsFalse()
    {
        bool result = _cooldownSystem.TriggerCooldown(99999);

        Assert.IsFalse(result);
    }

    [Test]
    public void TriggerCooldown_TriggersGcd_WhenAffectedByGcd()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f, true);
        _cooldownSystem.RegisterSkill(skillData);

        _cooldownSystem.TriggerCooldown(10001);

        Assert.IsTrue(_cooldownSystem.IsGcdActive);
    }

    [Test]
    public void TriggerCooldown_DoesNotTriggerGcd_WhenNotAffectedByGcd()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f, false);
        _cooldownSystem.RegisterSkill(skillData);

        _cooldownSystem.TriggerCooldown(10001);

        Assert.IsFalse(_cooldownSystem.IsGcdActive);
    }

    [Test]
    public void TriggerCooldown_UsesCustomGcd_WhenGcdOverrideSet()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f, true);
        skillData.GcdOverride = 2.0f;
        _cooldownSystem.RegisterSkill(skillData);

        _cooldownSystem.TriggerCooldown(10001);

        // GCD应该被触发（虽然无法精确验证时长，但可以验证状态）
        Assert.IsTrue(_cooldownSystem.IsGcdActive);
    }

    #endregion

    #region 充能测试

    [Test]
    public void GetCurrentCharges_NewSkill_ReturnsMaxCharges()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f, true, 3);
        _cooldownSystem.RegisterSkill(skillData);

        int charges = _cooldownSystem.GetCurrentCharges(10001);

        Assert.AreEqual(3, charges);
    }

    [Test]
    public void TriggerCooldown_ConsumesCharge_WhenHasCharges()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f, true, 3);
        _cooldownSystem.RegisterSkill(skillData);

        _cooldownSystem.TriggerCooldown(10001);

        int charges = _cooldownSystem.GetCurrentCharges(10001);
        Assert.AreEqual(2, charges);
    }

    [Test]
    public void CanUseSkill_ReturnsFalse_WhenNoCharges()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 0f, true, 2);
        _cooldownSystem.RegisterSkill(skillData);
        _cooldownSystem.TriggerCooldown(10001);
        _cooldownSystem.TriggerCooldown(10001);

        bool result = _cooldownSystem.CanUseSkill(10001);

        Assert.IsFalse(result);
    }

    #endregion

    #region 冷却重置测试

    [Test]
    public void ResetCooldown_ClearsCooldown()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f);
        _cooldownSystem.RegisterSkill(skillData);
        _cooldownSystem.TriggerCooldown(10001);

        _cooldownSystem.ResetCooldown(10001);

        Assert.IsTrue(_cooldownSystem.CanUseSkill(10001));
    }

    [Test]
    public void ResetCooldown_RestoresCharges()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 5f, true, 3);
        _cooldownSystem.RegisterSkill(skillData);
        _cooldownSystem.TriggerCooldown(10001);
        _cooldownSystem.TriggerCooldown(10001);

        _cooldownSystem.ResetCooldown(10001);

        Assert.AreEqual(3, _cooldownSystem.GetCurrentCharges(10001));
    }

    [Test]
    public void ResetAllCooldowns_ClearsAllCooldownsAndGcd()
    {
        var skill1 = CreateTestSkill(10001, "Skill1", 5f);
        var skill2 = CreateTestSkill(10002, "Skill2", 10f);
        _cooldownSystem.RegisterSkill(skill1);
        _cooldownSystem.RegisterSkill(skill2);
        _cooldownSystem.TriggerCooldown(10001);
        _cooldownSystem.TriggerCooldown(10002);

        _cooldownSystem.ResetAllCooldowns();

        Assert.IsTrue(_cooldownSystem.CanUseSkill(10001));
        Assert.IsTrue(_cooldownSystem.CanUseSkill(10002));
        Assert.IsFalse(_cooldownSystem.IsGcdActive);
    }

    #endregion

    #region 冷却减少测试

    [Test]
    public void ReduceCooldown_DecreasesRemainingTime()
    {
        var skillData = CreateTestSkill(10001, "TestSkill", 10f);
        _cooldownSystem.RegisterSkill(skillData);
        _cooldownSystem.TriggerCooldown(10001);

        float before = _cooldownSystem.GetRemainingCooldown(10001);
        _cooldownSystem.ReduceCooldown(10001, 5f);
        float after = _cooldownSystem.GetRemainingCooldown(10001);

        Assert.Less(after, before);
    }

    #endregion

    #region GCD测试

    [Test]
    public void TriggerGcd_SetsGcdActive()
    {
        _cooldownSystem.TriggerGcd(1.0f);

        Assert.IsTrue(_cooldownSystem.IsGcdActive);
        Assert.Greater(_cooldownSystem.GcdRemainingTime, 0f);
    }

    [Test]
    public void TriggerGcd_ZeroDuration_DoesNotActivate()
    {
        _cooldownSystem.TriggerGcd(0f);

        Assert.IsFalse(_cooldownSystem.IsGcdActive);
    }

    #endregion

    #region 辅助方法

    private SkillData CreateTestSkill(
        int skillId,
        string skillName,
        float cooldown,
        bool affectedByGcd = true,
        int maxCharges = 1)
    {
        return new SkillData
        {
            SkillId = skillId,
            SkillName = skillName,
            Description = $"Test skill {skillName}",
            SkillType = "active",
            Cooldown = cooldown,
            AffectedByGcd = affectedByGcd,
            GcdOverride = 0f,
            Priority = 1,
            MaxCharges = maxCharges,
            ChargeCooldown = 0f,
            Tags = new System.Collections.Generic.List<string> { "test" }
        };
    }

    #endregion
}
