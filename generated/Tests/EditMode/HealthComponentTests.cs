```csharp
// === Tests/EditMode/HealthComponentTests.cs
using NUnit.Framework;
using UnityEngine;

public class HealthComponentTests
{
    private GameObject _gameObject;
    private HealthComponent _healthComponent;

    [SetUp]
    public void SetUp()
    {
        _gameObject = new GameObject();
        _healthComponent = _gameObject.AddComponent<HealthComponent>();
    }

    [TearDown]
    public void TearDown()
    {
        Object.DestroyImmediate(_gameObject);
    }

    // Initialize
    [Test]
    public void Initialize_ValidMaxHp_SetsMaxAndCurrentHp()
    {
        _healthComponent.Initialize(100f);

        Assert.AreEqual(100f, _healthComponent.MaxHp);
        Assert.AreEqual(100f, _healthComponent.CurrentHp);
        Assert.IsFalse(_healthComponent.IsDead);
    }

    [Test]
    public void Initialize_ZeroMaxHp_SetsMaxAndCurrentHpToZeroAndIsDead()
    {
        _healthComponent.Initialize(0f);

        Assert.AreEqual(0f, _healthComponent.MaxHp);
        Assert.AreEqual(0f, _healthComponent.CurrentHp);
        Assert.IsTrue(_healthComponent.IsDead);
    }

    [Test]
    public void Initialize_NegativeMaxHp_SetsMaxAndCurrentHpToNegativeAndIsDead()
    {
        _healthComponent.Initialize(-50f);

        Assert.AreEqual(-50f, _healthComponent.MaxHp);
        Assert.AreEqual(-50f, _healthComponent.CurrentHp);
        Assert.IsTrue(_healthComponent.IsDead);
    }

    // TakeDamage
    [Test]
    public void TakeDamage_PositiveDamage_ReducesCurrentHp()
    {
        _healthComponent.Initialize(100f);
        
        _healthComponent.TakeDamage(30f);

        Assert.AreEqual(70f, _healthComponent.CurrentHp);
        Assert.IsFalse(_healthComponent.IsDead);
    }

    [Test]
    public void TakeDamage_DamageExceedsCurrentHp_ClampsToZeroAndInvokesOnDeath()
    {
        _healthComponent.Initialize(100f);
        bool deathInvoked = false;
        _healthComponent.OnDeath += () => deathInvoked = true;

        _healthComponent.TakeDamage(150f);

        Assert.AreEqual(0f, _healthComponent.CurrentHp);
        Assert.IsTrue(_healthComponent.IsDead);
        Assert.IsTrue(deathInvoked);
    }

    [Test]
    public void TakeDamage_WhenAlreadyDead_DoesNotChangeCurrentHpOrInvokeOnDeath()
    {
        _healthComponent.Initialize(100f);
        _healthComponent.TakeDamage(100f);
        bool deathInvoked = false;
        _healthComponent.OnDeath += () => deathInvoked = true;

        _healthComponent.TakeDamage(50f);

        Assert.AreEqual(0f, _healthComponent.CurrentHp);
        Assert.IsTrue(_healthComponent.IsDead);
        Assert.IsFalse(deathInvoked);
    }

    // Heal
    [Test]
    public