using UnityEngine;

/// <summary>ÑªÁ¿×é¼þ</summary>
public class HealthComponent : MonoBehaviour
{
    [SerializeField] private float _maxHp = 100f;
    private float _currentHp;

    public float CurrentHp => _currentHp;
    public float MaxHp => _maxHp;
    public bool IsDead => _currentHp <= 0;

    public event System.Action OnDeath;

    public void Initialize(float maxHp)
    {
        _maxHp = maxHp;
        _currentHp = maxHp;
    }

    public void TakeDamage(float damage)
    {
        if (IsDead) return;
        _currentHp = Mathf.Max(0, _currentHp - damage);
        if (IsDead) OnDeath?.Invoke();
    }

    public void Heal(float amount)
    {
        if (IsDead) return;
        _currentHp = Mathf.Min(_maxHp, _currentHp + amount);
    }
}
