using UnityEngine;
using UnityEngine.Events;

namespace Project.Skill
{
    /// <summary>
    /// 技能槽位组件，挂载到技能UI上，提供冷却状态查询和UI更新。
    /// </summary>
    public class SkillSlot : MonoBehaviour
    {
        #region 字段

        [Header("技能配置")]
        [SerializeField]
        [Tooltip("绑定的技能ID")]
        private int _skillId;

        [Header("UI组件引用")]
        [SerializeField]
        [Tooltip("冷却遮罩（用于显示冷却进度）")]
        private GameObject _cooldownOverlay;

        [SerializeField]
        [Tooltip("冷却进度条（0-1）")]
        private UnityEngine.UI.Image _cooldownProgressImage;

        [SerializeField]
        [Tooltip("充能数显示文本")]
        private TMPro.TextMeshProUGUI _chargeText;

        [Header("事件")]
        [SerializeField]
        private UnityEvent _onSkillReady;

        [SerializeField]
        private UnityEvent _onSkillCooldownStart;

        [SerializeField]
        private UnityEvent<int, int> _onChargeChanged;

        private SkillCooldownSystem _cooldownSystem;
        private bool _isSubscribed;
        private int _lastCharges = -1;

        #endregion

        #region 属性

        /// <summary>
        /// 绑定的技能ID。
        /// </summary>
        public int SkillId
        {
            get => _skillId;
            set
            {
                if (_skillId != value)
                {
                    UnsubscribeEvents();
                    _skillId = value;
                    SubscribeEvents();
                    RefreshUI();
                }
            }
        }

        /// <summary>
        /// 技能是否可以使用。
        /// </summary>
        public bool IsReady => _cooldownSystem != null && _cooldownSystem.CanUseSkill(_skillId);

        /// <summary>
        /// 剩余冷却时间（秒）。
        /// </summary>
        public float RemainingCooldown => _cooldownSystem?.GetRemainingCooldown(_skillId) ?? 0f;

        /// <summary>
        /// 冷却进度（0-1）。
        /// </summary>
        public float CooldownProgress => _cooldownSystem?.GetCooldownProgress(_skillId) ?? 1f;

        /// <summary>
        /// 当前充能数。
        /// </summary>
        public int CurrentCharges => _cooldownSystem?.GetCurrentCharges(_skillId) ?? 0;

        #endregion

        #region Unity生命周期

        private void Awake()
        {
            _cooldownSystem = SkillCooldownSystem.Instance;
        }

        private void OnEnable()
        {
            SubscribeEvents();
            RefreshUI();
        }

        private void OnDisable()
        {
            UnsubscribeEvents();
        }

        #endregion

        #region 公开方法

        /// <summary>
        /// 尝试使用技能。
        /// </summary>
        /// <returns>如果成功触发冷却则返回true。</returns>
        public bool UseSkill()
        {
            if (_cooldownSystem == null)
            {
                Debug.LogWarning($"[SkillSlot] CooldownSystem not initialized on {gameObject.name}");
                return false;
            }

            if (_cooldownSystem.TriggerCooldown(_skillId))
            {
                return true;
            }

            return false;
        }

        /// <summary>
        /// 刷新UI显示。
        /// </summary>
        public void RefreshUI()
        {
            if (_cooldownSystem == null) return;

            float progress = CooldownProgress;
            bool isReady = IsReady;
            int charges = CurrentCharges;

            // 更新冷却遮罩
            if (_cooldownOverlay != null)
            {
                _cooldownOverlay.SetActive(!isReady);
            }

            // 更新进度条
            if (_cooldownProgressImage != null)
            {
                _cooldownProgressImage.fillAmount = progress;
            }

            // 更新充能数
            if (_chargeText != null)
            {
                var skillData = _cooldownSystem.GetSkillData(_skillId);
                if (skillData != null && skillData.HasCharges())
                {
                    _chargeText.gameObject.SetActive(true);
                    _chargeText.text = charges.ToString();
                }
                else
                {
                    _chargeText.gameObject.SetActive(false);
                }
            }
        }

        /// <summary>
        /// 重置技能冷却。
        /// </summary>
        public void ResetCooldown()
        {
            if (_cooldownSystem != null)
            {
                _cooldownSystem.ResetCooldown(_skillId);
            }
        }

        #endregion

        #region 私有方法

        private void SubscribeEvents()
        {
            if (_isSubscribed || _cooldownSystem == null) return;

            _cooldownSystem.OnSkillCooldownEnded += HandleSkillCooldownEnded;
            _cooldownSystem.OnSkillCooldownStarted += HandleSkillCooldownStarted;
            _cooldownSystem.OnSkillChargeChanged += HandleChargeChanged;
            _cooldownSystem.OnGcdEnded += HandleGcdEnded;

            _isSubscribed = true;
        }

        private void UnsubscribeEvents()
        {
            if (!_isSubscribed || _cooldownSystem == null) return;

            _cooldownSystem.OnSkillCooldownEnded -= HandleSkillCooldownEnded;
            _cooldownSystem.OnSkillCooldownStarted -= HandleSkillCooldownStarted;
            _cooldownSystem.OnSkillChargeChanged -= HandleChargeChanged;
            _cooldownSystem.OnGcdEnded -= HandleGcdEnded;

            _isSubscribed = false;
        }

        private void HandleSkillCooldownEnded(int skillId)
        {
            if (skillId == _skillId)
            {
                RefreshUI();
                _onSkillReady?.Invoke();
            }
        }

        private void HandleSkillCooldownStarted(int skillId, float duration)
        {
            if (skillId == _skillId)
            {
                RefreshUI();
                _onSkillCooldownStart?.Invoke();
            }
        }

        private void HandleChargeChanged(int skillId, int current, int max)
        {
            if (skillId == _skillId)
            {
                _lastCharges = current;
                RefreshUI();
                _onChargeChanged?.Invoke(current, max);
            }
        }

        private void HandleGcdEnded()
        {
            // GCD结束可能影响技能可用性，刷新UI
            RefreshUI();
        }

        #endregion

        #region 编辑器辅助

#if UNITY_EDITOR
        private void OnValidate()
        {
            if (Application.isPlaying && _cooldownSystem != null)
            {
                RefreshUI();
            }
        }
#endif

        #endregion
    }
}
