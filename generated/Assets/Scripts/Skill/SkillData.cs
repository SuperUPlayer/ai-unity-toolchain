using System;
using System.Collections.Generic;

namespace Project.Skill
{
    /// <summary>
    /// 技能数据结构，定义技能的冷却时间、GCD影响等配置。
    /// 可从JSON配置文件加载或通过代码创建。
    /// </summary>
    [Serializable]
    public class SkillData
    {
        /// <summary>
        /// 技能唯一标识符。
        /// </summary>
        public int SkillId;

        /// <summary>
        /// 技能名称。
        /// </summary>
        public string SkillName;

        /// <summary>
        /// 技能描述。
        /// </summary>
        public string Description;

        /// <summary>
        /// 技能类型（active、passive、auto_attack等）。
        /// </summary>
        public string SkillType;

        /// <summary>
        /// 技能独立冷却时间（秒）。
        /// </summary>
        public float Cooldown;

        /// <summary>
        /// 是否受全局公共冷却时间（GCD）影响。
        /// </summary>
        public bool AffectedByGcd;

        /// <summary>
        /// 自定义GCD时长（秒）。0表示使用默认GCD。
        /// </summary>
        public float GcdOverride;

        /// <summary>
        /// 技能优先级（数值越小优先级越高）。
        /// </summary>
        public int Priority;

        /// <summary>
        /// 最大充能层数。1表示无充能机制。
        /// </summary>
        public int MaxCharges;

        /// <summary>
        /// 每层充能的恢复时间（秒）。0表示使用Cooldown字段。
        /// </summary>
        public float ChargeCooldown;

        /// <summary>
        /// 技能标签列表，用于分类和筛选。
        /// </summary>
        public List<string> Tags;

        /// <summary>
        /// 默认构造函数。
        /// </summary>
        public SkillData()
        {
            SkillId = 0;
            SkillName = string.Empty;
            Description = string.Empty;
            SkillType = "active";
            Cooldown = 0f;
            AffectedByGcd = true;
            GcdOverride = 0f;
            Priority = 1;
            MaxCharges = 1;
            ChargeCooldown = 0f;
            Tags = new List<string>();
        }

        /// <summary>
        /// 获取实际的充能恢复时间。
        /// 如果ChargeCooldown为0，则返回Cooldown。
        /// </summary>
        /// <returns>充能恢复时间（秒）。</returns>
        public float GetActualChargeCooldown()
        {
            return ChargeCooldown > 0f ? ChargeCooldown : Cooldown;
        }

        /// <summary>
        /// 检查技能是否支持充能机制。
        /// </summary>
        /// <returns>如果MaxCharges大于1则返回true。</returns>
        public bool HasCharges()
        {
            return MaxCharges > 1;
        }
    }

    /// <summary>
    /// 技能冷却状态，记录单个技能的实时冷却信息。
    /// </summary>
    public class SkillCooldownState
    {
        private readonly int _skillId;
        private float _cooldownEndTime;
        private int _currentCharges;
        private float _nextChargeRecoverTime;

        /// <summary>
        /// 技能ID。
        /// </summary>
        public int SkillId => _skillId;

        /// <summary>
        /// 冷却结束时间（Time.time）。
        /// </summary>
        public float CooldownEndTime => _cooldownEndTime;

        /// <summary>
        /// 当前充能层数。
        /// </summary>
        public int CurrentCharges => _currentCharges;

        /// <summary>
        /// 下一层充能恢复时间（Time.time）。
        /// </summary>
        public float NextChargeRecoverTime => _nextChargeRecoverTime;

        /// <summary>
        /// 构造函数。
        /// </summary>
        /// <param name="skillId">技能ID。</param>
        /// <param name="maxCharges">最大充能层数。</param>
        public SkillCooldownState(int skillId, int maxCharges)
        {
            _skillId = skillId;
            _currentCharges = maxCharges;
            _cooldownEndTime = 0f;
            _nextChargeRecoverTime = 0f;
        }

        /// <summary>
        /// 设置冷却结束时间。
        /// </summary>
        /// <param name="endTime">冷却结束时间。</param>
        public void SetCooldownEndTime(float endTime)
        {
            _cooldownEndTime = endTime;
        }

        /// <summary>
        /// 消耗一层充能。
        /// </summary>
        /// <param name="recoverTime">充能恢复时间。</param>
        public void ConsumeCharge(float recoverTime)
        {
            if (_currentCharges > 0)
            {
                _currentCharges--;
                if (_currentCharges < 1 && recoverTime > 0f)
                {
                    _nextChargeRecoverTime = UnityEngine.Time.time + recoverTime;
                }
            }
        }

        /// <summary>
        /// 恢复一层充能。
        /// </summary>
        /// <param name="maxCharges">最大充能层数。</param>
        /// <param name="nextRecoverTime">下一次恢复时间。</param>
        public void RecoverCharge(int maxCharges, float nextRecoverTime)
        {
            if (_currentCharges < maxCharges)
            {
                _currentCharges++;
                _nextChargeRecoverTime = _currentCharges >= maxCharges ? 0f : nextRecoverTime;
            }
        }

        /// <summary>
        /// 设置下一层充能恢复时间。
        /// </summary>
        /// <param name="recoverTime">恢复时间。</param>
        public void SetNextChargeRecoverTime(float recoverTime)
        {
            _nextChargeRecoverTime = recoverTime;
        }

        /// <summary>
        /// 重置冷却状态（满充能，无冷却）。
        /// </summary>
        /// <param name="maxCharges">最大充能层数。</param>
        public void Reset(int maxCharges)
        {
            _currentCharges = maxCharges;
            _cooldownEndTime = 0f;
            _nextChargeRecoverTime = 0f;
        }
    }
}
