using System.Collections.Generic;
using UnityEngine;

namespace Project.Skill
{
    /// <summary>
    /// 技能冷却系统，管理全局公共冷却时间（GCD）和技能独立冷却。
    /// 继承自Singleton，提供全局访问点。
    /// </summary>
    public class SkillCooldownSystem : Singleton<SkillCooldownSystem>
    {
        #region 字段

        [Header("GCD配置")]
        [SerializeField]
        [Tooltip("默认全局公共冷却时间（秒）")]
        private float _defaultGcdDuration = 1.0f;

        private float _gcdEndTime;
        private readonly Dictionary<int, SkillData> _skillDataDict = new Dictionary<int, SkillData>();
        private readonly Dictionary<int, SkillCooldownState> _cooldownStates = new Dictionary<int, SkillCooldownState>();

        #endregion

        #region 属性

        /// <summary>
        /// 默认GCD时长（秒）。
        /// </summary>
        public float DefaultGcdDuration => _defaultGcdDuration;

        /// <summary>
        /// GCD是否正在冷却中。
        /// </summary>
        public bool IsGcdActive => Time.time < _gcdEndTime;

        /// <summary>
        /// GCD剩余冷却时间（秒）。
        /// </summary>
        public float GcdRemainingTime => Mathf.Max(0f, _gcdEndTime - Time.time);

        #endregion

        #region 事件

        /// <summary>
        /// GCD开始时触发。
        /// </summary>
        public event System.Action<float> OnGcdStarted;

        /// <summary>
        /// GCD结束时触发。
        /// </summary>
        public event System.Action OnGcdEnded;

        /// <summary>
        /// 技能冷却开始时触发。参数：技能ID，冷却时长。
        /// </summary>
        public event System.Action<int, float> OnSkillCooldownStarted;

        /// <summary>
        /// 技能冷却结束时触发。参数：技能ID。
        /// </summary>
        public event System.Action<int> OnSkillCooldownEnded;

        /// <summary>
        /// 技能充能变化时触发。参数：技能ID，当前充能数，最大充能数。
        /// </summary>
        public event System.Action<int, int, int> OnSkillChargeChanged;

        #endregion

        #region Unity生命周期

        protected override void Awake()
        {
            base.Awake();
            _gcdEndTime = 0f;
        }

        private void Update()
        {
            UpdateGcd();
            UpdateChargeRecovery();
        }

        protected override void OnDestroy()
        {
            OnGcdStarted = null;
            OnGcdEnded = null;
            OnSkillCooldownStarted = null;
            OnSkillCooldownEnded = null;
            OnSkillChargeChanged = null;
            base.OnDestroy();
        }

        #endregion

        #region 公开方法 - 技能数据管理

        /// <summary>
        /// 注册技能数据。
        /// </summary>
        /// <param name="skillData">技能数据。</param>
        public void RegisterSkill(SkillData skillData)
        {
            if (skillData == null)
            {
                Debug.LogWarning("[SkillCooldownSystem] Cannot register null skill data.");
                return;
            }

            if (_skillDataDict.ContainsKey(skillData.SkillId))
            {
                Debug.LogWarning($"[SkillCooldownSystem] Skill {skillData.SkillId} already registered. Overwriting.");
            }

            _skillDataDict[skillData.SkillId] = skillData;

            // 初始化冷却状态
            if (!_cooldownStates.ContainsKey(skillData.SkillId))
            {
                _cooldownStates[skillData.SkillId] = new SkillCooldownState(skillData.SkillId, skillData.MaxCharges);
            }
        }

        /// <summary>
        /// 批量注册技能数据。
        /// </summary>
        /// <param name="skillDataList">技能数据列表。</param>
        public void RegisterSkills(IEnumerable<SkillData> skillDataList)
        {
            if (skillDataList == null) return;

            foreach (var skillData in skillDataList)
            {
                RegisterSkill(skillData);
            }
        }

        /// <summary>
        /// 获取技能数据。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <returns>技能数据，如果不存在则返回null。</returns>
        public SkillData GetSkillData(int skillId)
        {
            _skillDataDict.TryGetValue(skillId, out var skillData);
            return skillData;
        }

        /// <summary>
        /// 获取技能冷却状态。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <returns>冷却状态，如果不存在则返回null。</returns>
        public SkillCooldownState GetCooldownState(int skillId)
        {
            _cooldownStates.TryGetValue(skillId, out var state);
            return state;
        }

        #endregion

        #region 公开方法 - 冷却查询

        /// <summary>
        /// 检查技能是否可以使用。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <returns>如果技能可以使用则返回true。</returns>
        public bool CanUseSkill(int skillId)
        {
            if (!_skillDataDict.TryGetValue(skillId, out var skillData))
            {
                return false;
            }

            if (!_cooldownStates.TryGetValue(skillId, out var state))
            {
                return false;
            }

            // 检查充能
            if (skillData.HasCharges() && state.CurrentCharges <= 0)
            {
                return false;
            }

            // 检查独立冷却
            if (Time.time < state.CooldownEndTime)
            {
                return false;
            }

            // 检查GCD
            if (skillData.AffectedByGcd && IsGcdActive)
            {
                return false;
            }

            return true;
        }

        /// <summary>
        /// 获取技能剩余冷却时间。
        /// 综合考虑独立冷却和GCD。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <returns>剩余冷却时间（秒）。</returns>
        public float GetRemainingCooldown(int skillId)
        {
            float remaining = 0f;

            if (_cooldownStates.TryGetValue(skillId, out var state))
            {
                remaining = Mathf.Max(remaining, state.CooldownEndTime - Time.time);
            }

            if (_skillDataDict.TryGetValue(skillId, out var skillData) && skillData.AffectedByGcd)
            {
                remaining = Mathf.Max(remaining, GcdRemainingTime);
            }

            return Mathf.Max(0f, remaining);
        }

        /// <summary>
        /// 获取技能冷却进度（0-1）。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <returns>冷却进度，1表示已就绪，0表示刚开始冷却。</returns>
        public float GetCooldownProgress(int skillId)
        {
            if (!_skillDataDict.TryGetValue(skillId, out var skillData))
            {
                return 1f;
            }

            float totalCooldown = skillData.Cooldown;
            if (totalCooldown <= 0f)
            {
                return 1f;
            }

            float remaining = GetRemainingCooldown(skillId);
            return 1f - (remaining / totalCooldown);
        }

        /// <summary>
        /// 获取技能当前充能数。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <returns>当前充能数，如果技能不存在则返回0。</returns>
        public int GetCurrentCharges(int skillId)
        {
            if (_cooldownStates.TryGetValue(skillId, out var state))
            {
                return state.CurrentCharges;
            }
            return 0;
        }

        #endregion

        #region 公开方法 - 冷却控制

        /// <summary>
        /// 触发技能冷却。
        /// 调用此方法表示技能已被使用，开始冷却计时。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <returns>如果成功触发冷却则返回true。</returns>
        public bool TriggerCooldown(int skillId)
        {
            if (!_skillDataDict.TryGetValue(skillId, out var skillData))
            {
                Debug.LogWarning($"[SkillCooldownSystem] Skill {skillId} not found.");
                return false;
            }

            if (!_cooldownStates.TryGetValue(skillId, out var state))
            {
                state = new SkillCooldownState(skillId, skillData.MaxCharges);
                _cooldownStates[skillId] = state;
            }

            // 检查是否可用
            if (!CanUseSkill(skillId))
            {
                return false;
            }

            // 触发GCD
            if (skillData.AffectedByGcd)
            {
                float gcdDuration = skillData.GcdOverride > 0f ? skillData.GcdOverride : _defaultGcdDuration;
                TriggerGcd(gcdDuration);
            }

            // 处理充能技能
            if (skillData.HasCharges())
            {
                state.ConsumeCharge(skillData.GetActualChargeCooldown());
                OnSkillChargeChanged?.Invoke(skillId, state.CurrentCharges, skillData.MaxCharges);
            }

            // 设置独立冷却
            if (skillData.Cooldown > 0f)
            {
                float cooldownEnd = Time.time + skillData.Cooldown;
                state.SetCooldownEndTime(cooldownEnd);
                OnSkillCooldownStarted?.Invoke(skillId, skillData.Cooldown);
            }

            return true;
        }

        /// <summary>
        /// 手动触发全局公共冷却时间。
        /// </summary>
        /// <param name="duration">GCD时长（秒）。</param>
        public void TriggerGcd(float duration)
        {
            if (duration <= 0f) return;

            bool wasActive = IsGcdActive;
            _gcdEndTime = Time.time + duration;

            if (!wasActive)
            {
                OnGcdStarted?.Invoke(duration);
            }
        }

        /// <summary>
        /// 重置技能冷却（立即就绪）。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        public void ResetCooldown(int skillId)
        {
            if (_cooldownStates.TryGetValue(skillId, out var state))
            {
                if (_skillDataDict.TryGetValue(skillId, out var skillData))
                {
                    state.Reset(skillData.MaxCharges);
                    OnSkillChargeChanged?.Invoke(skillId, state.CurrentCharges, skillData.MaxCharges);
                }
                OnSkillCooldownEnded?.Invoke(skillId);
            }
        }

        /// <summary>
        /// 重置所有技能冷却。
        /// </summary>
        public void ResetAllCooldowns()
        {
            foreach (var kvp in _cooldownStates)
            {
                int skillId = kvp.Key;
                var state = kvp.Value;
                if (_skillDataDict.TryGetValue(skillId, out var skillData))
                {
                    state.Reset(skillData.MaxCharges);
                    OnSkillChargeChanged?.Invoke(skillId, state.CurrentCharges, skillData.MaxCharges);
                }
                OnSkillCooldownEnded?.Invoke(skillId);
            }

            _gcdEndTime = 0f;
            OnGcdEnded?.Invoke();
        }

        /// <summary>
        /// 减少技能冷却时间。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <param name="seconds">减少的秒数。</param>
        public void ReduceCooldown(int skillId, float seconds)
        {
            if (_cooldownStates.TryGetValue(skillId, out var state))
            {
                float newEndTime = state.CooldownEndTime - seconds;
                state.SetCooldownEndTime(Mathf.Max(Time.time, newEndTime));

                // 减少充能恢复时间
                if (state.NextChargeRecoverTime > 0f)
                {
                    float newRecoverTime = state.NextChargeRecoverTime - seconds;
                    state.SetNextChargeRecoverTime(Mathf.Max(Time.time, newRecoverTime));
                }
            }
        }

        #endregion

        #region 私有方法

        private void UpdateGcd()
        {
            if (_gcdEndTime > 0f && Time.time >= _gcdEndTime)
            {
                _gcdEndTime = 0f;
                OnGcdEnded?.Invoke();
            }
        }

        private void UpdateChargeRecovery()
        {
            foreach (var kvp in _cooldownStates)
            {
                int skillId = kvp.Key;
                var state = kvp.Value;

                if (state.NextChargeRecoverTime > 0f && Time.time >= state.NextChargeRecoverTime)
                {
                    if (_skillDataDict.TryGetValue(skillId, out var skillData))
                    {
                        float nextRecoverTime = Time.time + skillData.GetActualChargeCooldown();
                        state.RecoverCharge(skillData.MaxCharges, nextRecoverTime);
                        OnSkillChargeChanged?.Invoke(skillId, state.CurrentCharges, skillData.MaxCharges);

                        // 检查独立冷却是否结束
                        if (Time.time >= state.CooldownEndTime && state.CurrentCharges > 0)
                        {
                            OnSkillCooldownEnded?.Invoke(skillId);
                        }
                    }
                }
            }
        }

        #endregion
    }
}
