package rules;

import com.google.common.base.MoreObjects;
import com.google.common.primitives.Booleans;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import com.google.errorprone.annotations.Var;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;
import javax.annotation.ParametersAreNonnullByDefault;
import javax.annotation.concurrent.Immutable;
import javax.annotation.concurrent.NotThreadSafe;
import org.apache.calcite.plan.RelRule;
import org.apache.calcite.tools.RelBuilderFactory;
import org.immutables.value.Generated;

/**
 * Immutable implementation of {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig}.
 * <p>
 * Use the builder to create immutable instances:
 * {@code ImmutableMyJoinReduceExpressionsRuleConfig.builder()}.
 * Use the static factory method to get the default singleton instance:
 * {@code ImmutableMyJoinReduceExpressionsRuleConfig.of()}.
 */
@Generated(from = "MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig", generator = "Immutables")
@SuppressWarnings({"all"})
@ParametersAreNonnullByDefault
@javax.annotation.processing.Generated("org.immutables.processor.ProxyProcessor")
@Immutable
@CheckReturnValue
final class ImmutableMyJoinReduceExpressionsRuleConfig
        implements MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig {
    private final RelBuilderFactory relBuilderFactory;
    private final @Nullable java.lang.@org.checkerframework.checker.nullness.qual.Nullable String description;
    private final RelRule.OperandTransform operandSupplier;
    private final boolean matchNullability;
    private final boolean treatDynamicCallsAsConstant;

    private ImmutableMyJoinReduceExpressionsRuleConfig() {
        this.description = null;
        this.relBuilderFactory = initShim.relBuilderFactory();
        this.operandSupplier = initShim.operandSupplier();
        this.matchNullability = initShim.matchNullability();
        this.treatDynamicCallsAsConstant = initShim.treatDynamicCallsAsConstant();
        this.initShim = null;
    }

    private ImmutableMyJoinReduceExpressionsRuleConfig(ImmutableMyJoinReduceExpressionsRuleConfig.Builder builder) {
        this.description = builder.description;
        if (builder.relBuilderFactory != null) {
            initShim.withRelBuilderFactory(builder.relBuilderFactory);
        }
        if (builder.operandSupplier != null) {
            initShim.withOperandSupplier(builder.operandSupplier);
        }
        if (builder.matchNullabilityIsSet()) {
            initShim.withMatchNullability(builder.matchNullability);
        }
        if (builder.treatDynamicCallsAsConstantIsSet()) {
            initShim.withTreatDynamicCallsAsConstant(builder.treatDynamicCallsAsConstant);
        }
        this.relBuilderFactory = initShim.relBuilderFactory();
        this.operandSupplier = initShim.operandSupplier();
        this.matchNullability = initShim.matchNullability();
        this.treatDynamicCallsAsConstant = initShim.treatDynamicCallsAsConstant();
        this.initShim = null;
    }

    private ImmutableMyJoinReduceExpressionsRuleConfig(
            RelBuilderFactory relBuilderFactory,
            @Nullable java.lang.@org.checkerframework.checker.nullness.qual.Nullable String description,
            RelRule.OperandTransform operandSupplier,
            boolean matchNullability,
            boolean treatDynamicCallsAsConstant) {
        this.relBuilderFactory = relBuilderFactory;
        this.description = description;
        this.operandSupplier = operandSupplier;
        this.matchNullability = matchNullability;
        this.treatDynamicCallsAsConstant = treatDynamicCallsAsConstant;
        this.initShim = null;
    }

    private static final byte STAGE_INITIALIZING = -1;
    private static final byte STAGE_UNINITIALIZED = 0;
    private static final byte STAGE_INITIALIZED = 1;
    @SuppressWarnings("Immutable")
    private transient volatile InitShim initShim = new InitShim();

    @Generated(from = "MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig", generator = "Immutables")
    private final class InitShim {
        private byte relBuilderFactoryBuildStage = STAGE_UNINITIALIZED;
        private RelBuilderFactory relBuilderFactory;

        RelBuilderFactory relBuilderFactory() {
            if (relBuilderFactoryBuildStage == STAGE_INITIALIZING) throw new IllegalStateException(formatInitCycleMessage());
            if (relBuilderFactoryBuildStage == STAGE_UNINITIALIZED) {
                relBuilderFactoryBuildStage = STAGE_INITIALIZING;
                this.relBuilderFactory = Objects.requireNonNull(relBuilderFactoryInitialize(), "relBuilderFactory");
                relBuilderFactoryBuildStage = STAGE_INITIALIZED;
            }
            return this.relBuilderFactory;
        }

        void withRelBuilderFactory(RelBuilderFactory relBuilderFactory) {
            this.relBuilderFactory = relBuilderFactory;
            relBuilderFactoryBuildStage = STAGE_INITIALIZED;
        }

        private byte operandSupplierBuildStage = STAGE_UNINITIALIZED;
        private RelRule.OperandTransform operandSupplier;

        RelRule.OperandTransform operandSupplier() {
            if (operandSupplierBuildStage == STAGE_INITIALIZING) throw new IllegalStateException(formatInitCycleMessage());
            if (operandSupplierBuildStage == STAGE_UNINITIALIZED) {
                operandSupplierBuildStage = STAGE_INITIALIZING;
                this.operandSupplier = Objects.requireNonNull(operandSupplierInitialize(), "operandSupplier");
                operandSupplierBuildStage = STAGE_INITIALIZED;
            }
            return this.operandSupplier;
        }

        void withOperandSupplier(RelRule.OperandTransform operandSupplier) {
            this.operandSupplier = operandSupplier;
            operandSupplierBuildStage = STAGE_INITIALIZED;
        }

        private byte matchNullabilityBuildStage = STAGE_UNINITIALIZED;
        private boolean matchNullability;

        boolean matchNullability() {
            if (matchNullabilityBuildStage == STAGE_INITIALIZING) throw new IllegalStateException(formatInitCycleMessage());
            if (matchNullabilityBuildStage == STAGE_UNINITIALIZED) {
                matchNullabilityBuildStage = STAGE_INITIALIZING;
                this.matchNullability = matchNullabilityInitialize();
                matchNullabilityBuildStage = STAGE_INITIALIZED;
            }
            return this.matchNullability;
        }

        void withMatchNullability(boolean matchNullability) {
            this.matchNullability = matchNullability;
            matchNullabilityBuildStage = STAGE_INITIALIZED;
        }

        private byte treatDynamicCallsAsConstantBuildStage = STAGE_UNINITIALIZED;
        private boolean treatDynamicCallsAsConstant;

        boolean treatDynamicCallsAsConstant() {
            if (treatDynamicCallsAsConstantBuildStage == STAGE_INITIALIZING) throw new IllegalStateException(formatInitCycleMessage());
            if (treatDynamicCallsAsConstantBuildStage == STAGE_UNINITIALIZED) {
                treatDynamicCallsAsConstantBuildStage = STAGE_INITIALIZING;
                this.treatDynamicCallsAsConstant = treatDynamicCallsAsConstantInitialize();
                treatDynamicCallsAsConstantBuildStage = STAGE_INITIALIZED;
            }
            return this.treatDynamicCallsAsConstant;
        }

        void withTreatDynamicCallsAsConstant(boolean treatDynamicCallsAsConstant) {
            this.treatDynamicCallsAsConstant = treatDynamicCallsAsConstant;
            treatDynamicCallsAsConstantBuildStage = STAGE_INITIALIZED;
        }

        private String formatInitCycleMessage() {
            List<String> attributes = new ArrayList<>();
            if (relBuilderFactoryBuildStage == STAGE_INITIALIZING) attributes.add("relBuilderFactory");
            if (operandSupplierBuildStage == STAGE_INITIALIZING) attributes.add("operandSupplier");
            if (matchNullabilityBuildStage == STAGE_INITIALIZING) attributes.add("matchNullability");
            if (treatDynamicCallsAsConstantBuildStage == STAGE_INITIALIZING) attributes.add("treatDynamicCallsAsConstant");
            return "Cannot build MyJoinReduceExpressionsRuleConfig, attribute initializers form cycle " + attributes;
        }
    }

    private RelBuilderFactory relBuilderFactoryInitialize() {
        return MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig.super.relBuilderFactory();
    }

    private RelRule.OperandTransform operandSupplierInitialize() {
        return MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig.super.operandSupplier();
    }

    private boolean matchNullabilityInitialize() {
        return MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig.super.matchNullability();
    }

    private boolean treatDynamicCallsAsConstantInitialize() {
        return MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig.super.treatDynamicCallsAsConstant();
    }

    /**
     * @return The value of the {@code relBuilderFactory} attribute
     */
    @Override
    public RelBuilderFactory relBuilderFactory() {
        InitShim shim = this.initShim;
        return shim != null
                ? shim.relBuilderFactory()
                : this.relBuilderFactory;
    }

    /**
     * @return The value of the {@code description} attribute
     */
    @Override
    public @Nullable java.lang.@org.checkerframework.checker.nullness.qual.Nullable String description() {
        return description;
    }

    /**
     * @return The value of the {@code operandSupplier} attribute
     */
    @Override
    public RelRule.OperandTransform operandSupplier() {
        InitShim shim = this.initShim;
        return shim != null
                ? shim.operandSupplier()
                : this.operandSupplier;
    }

    /**
     * @return The value of the {@code matchNullability} attribute
     */
    @Override
    public boolean matchNullability() {
        InitShim shim = this.initShim;
        return shim != null
                ? shim.matchNullability()
                : this.matchNullability;
    }

    /**
     * @return The value of the {@code treatDynamicCallsAsConstant} attribute
     */
    @Override
    public boolean treatDynamicCallsAsConstant() {
        InitShim shim = this.initShim;
        return shim != null
                ? shim.treatDynamicCallsAsConstant()
                : this.treatDynamicCallsAsConstant;
    }

    /**
     * Copy the current immutable object by setting a value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#relBuilderFactory() relBuilderFactory} attribute.
     * A shallow reference equality check is used to prevent copying of the same value by returning {@code this}.
     * @param value A new value for relBuilderFactory
     * @return A modified copy of the {@code this} object
     */
    public final ImmutableMyJoinReduceExpressionsRuleConfig withRelBuilderFactory(RelBuilderFactory value) {
        if (this.relBuilderFactory == value) return this;
        RelBuilderFactory newValue = Objects.requireNonNull(value, "relBuilderFactory");
        return validate(new ImmutableMyJoinReduceExpressionsRuleConfig(
                newValue,
                this.description,
                this.operandSupplier,
                this.matchNullability,
                this.treatDynamicCallsAsConstant));
    }

    /**
     * Copy the current immutable object by setting a value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#description() description} attribute.
     * An equals check used to prevent copying of the same value by returning {@code this}.
     * @param value A new value for description (can be {@code null})
     * @return A modified copy of the {@code this} object
     */
    public final ImmutableMyJoinReduceExpressionsRuleConfig withDescription(@Nullable java.lang.@org.checkerframework.checker.nullness.qual.Nullable String value) {
        if (Objects.equals(this.description, value)) return this;
        return validate(new ImmutableMyJoinReduceExpressionsRuleConfig(
                this.relBuilderFactory,
                value,
                this.operandSupplier,
                this.matchNullability,
                this.treatDynamicCallsAsConstant));
    }

    /**
     * Copy the current immutable object by setting a value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#operandSupplier() operandSupplier} attribute.
     * A shallow reference equality check is used to prevent copying of the same value by returning {@code this}.
     * @param value A new value for operandSupplier
     * @return A modified copy of the {@code this} object
     */
    public final ImmutableMyJoinReduceExpressionsRuleConfig withOperandSupplier(RelRule.OperandTransform value) {
        if (this.operandSupplier == value) return this;
        RelRule.OperandTransform newValue = Objects.requireNonNull(value, "operandSupplier");
        return validate(new ImmutableMyJoinReduceExpressionsRuleConfig(
                this.relBuilderFactory,
                this.description,
                newValue,
                this.matchNullability,
                this.treatDynamicCallsAsConstant));
    }

    /**
     * Copy the current immutable object by setting a value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#matchNullability() matchNullability} attribute.
     * A value equality check is used to prevent copying of the same value by returning {@code this}.
     * @param value A new value for matchNullability
     * @return A modified copy of the {@code this} object
     */
    public final ImmutableMyJoinReduceExpressionsRuleConfig withMatchNullability(boolean value) {
        if (this.matchNullability == value) return this;
        return validate(new ImmutableMyJoinReduceExpressionsRuleConfig(
                this.relBuilderFactory,
                this.description,
                this.operandSupplier,
                value,
                this.treatDynamicCallsAsConstant));
    }

    /**
     * Copy the current immutable object by setting a value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#treatDynamicCallsAsConstant() treatDynamicCallsAsConstant} attribute.
     * A value equality check is used to prevent copying of the same value by returning {@code this}.
     * @param value A new value for treatDynamicCallsAsConstant
     * @return A modified copy of the {@code this} object
     */
    public final ImmutableMyJoinReduceExpressionsRuleConfig withTreatDynamicCallsAsConstant(boolean value) {
        if (this.treatDynamicCallsAsConstant == value) return this;
        return validate(new ImmutableMyJoinReduceExpressionsRuleConfig(this.relBuilderFactory, this.description, this.operandSupplier, this.matchNullability, value));
    }

    /**
     * This instance is equal to all instances of {@code ImmutableMyJoinReduceExpressionsRuleConfig} that have equal attribute values.
     * @return {@code true} if {@code this} is equal to {@code another} instance
     */
    @Override
    public boolean equals(@Nullable Object another) {
        if (this == another) return true;
        return another instanceof ImmutableMyJoinReduceExpressionsRuleConfig
                && equalTo((ImmutableMyJoinReduceExpressionsRuleConfig) another);
    }

    private boolean equalTo(ImmutableMyJoinReduceExpressionsRuleConfig another) {
        return relBuilderFactory.equals(another.relBuilderFactory)
                && Objects.equals(description, another.description)
                && operandSupplier.equals(another.operandSupplier)
                && matchNullability == another.matchNullability
                && treatDynamicCallsAsConstant == another.treatDynamicCallsAsConstant;
    }

    /**
     * Computes a hash code from attributes: {@code relBuilderFactory}, {@code description}, {@code operandSupplier}, {@code matchNullability}, {@code treatDynamicCallsAsConstant}.
     * @return hashCode value
     */
    @Override
    public int hashCode() {
        @Var int h = 5381;
        h += (h << 5) + relBuilderFactory.hashCode();
        h += (h << 5) + Objects.hashCode(description);
        h += (h << 5) + operandSupplier.hashCode();
        h += (h << 5) + Booleans.hashCode(matchNullability);
        h += (h << 5) + Booleans.hashCode(treatDynamicCallsAsConstant);
        return h;
    }

    /**
     * Prints the immutable value {@code MyJoinReduceExpressionsRuleConfig} with attribute values.
     * @return A string representation of the value
     */
    @Override
    public String toString() {
        return MoreObjects.toStringHelper("MyJoinReduceExpressionsRuleConfig")
                .omitNullValues()
                .add("relBuilderFactory", relBuilderFactory)
                .add("description", description)
                .add("operandSupplier", operandSupplier)
                .add("matchNullability", matchNullability)
                .add("treatDynamicCallsAsConstant", treatDynamicCallsAsConstant)
                .toString();
    }

    private static final ImmutableMyJoinReduceExpressionsRuleConfig INSTANCE = validate(new ImmutableMyJoinReduceExpressionsRuleConfig());

    /**
     * Returns the default immutable singleton value of {@code MyJoinReduceExpressionsRuleConfig}
     * @return An immutable instance of MyJoinReduceExpressionsRuleConfig
     */
    public static ImmutableMyJoinReduceExpressionsRuleConfig of() {
        return INSTANCE;
    }

    private static ImmutableMyJoinReduceExpressionsRuleConfig validate(ImmutableMyJoinReduceExpressionsRuleConfig instance) {
        return INSTANCE != null && INSTANCE.equalTo(instance) ? INSTANCE : instance;
    }

    /**
     * Creates an immutable copy of a {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig} value.
     * Uses accessors to get values to initialize the new immutable instance.
     * If an instance is already immutable, it is returned as is.
     * @param instance The instance to copy
     * @return A copied immutable MyJoinReduceExpressionsRuleConfig instance
     */
    public static ImmutableMyJoinReduceExpressionsRuleConfig copyOf(MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig instance) {
        if (instance instanceof ImmutableMyJoinReduceExpressionsRuleConfig) {
            return (ImmutableMyJoinReduceExpressionsRuleConfig) instance;
        }
        return ImmutableMyJoinReduceExpressionsRuleConfig.builder()
                .from(instance)
                .build();
    }

    /**
     * Creates a builder for {@link ImmutableMyJoinReduceExpressionsRuleConfig ImmutableMyJoinReduceExpressionsRuleConfig}.
     * <pre>
     * ImmutableMyJoinReduceExpressionsRuleConfig.builder()
     *    .withRelBuilderFactory(org.apache.calcite.tools.RelBuilderFactory) // optional {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#relBuilderFactory() relBuilderFactory}
     *    .withDescription(@org.checkerframework.checker.nullness.qual.Nullable String | null) // nullable {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#description() description}
     *    .withOperandSupplier(org.apache.calcite.plan.RelRule.OperandTransform) // optional {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#operandSupplier() operandSupplier}
     *    .withMatchNullability(boolean) // optional {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#matchNullability() matchNullability}
     *    .withTreatDynamicCallsAsConstant(boolean) // optional {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#treatDynamicCallsAsConstant() treatDynamicCallsAsConstant}
     *    .build();
     * </pre>
     * @return A new ImmutableMyJoinReduceExpressionsRuleConfig builder
     */
    public static ImmutableMyJoinReduceExpressionsRuleConfig.Builder builder() {
        return new ImmutableMyJoinReduceExpressionsRuleConfig.Builder();
    }

    /**
     * Builds instances of type {@link ImmutableMyJoinReduceExpressionsRuleConfig ImmutableMyJoinReduceExpressionsRuleConfig}.
     * Initialize attributes and then invoke the {@link #build()} method to create an
     * immutable instance.
     * <p><em>{@code Builder} is not thread-safe and generally should not be stored in a field or collection,
     * but instead used immediately to create instances.</em>
     */
    @Generated(from = "MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig", generator = "Immutables")
    @NotThreadSafe
    public static final class Builder {
        private static final long OPT_BIT_MATCH_NULLABILITY = 0x1L;
        private static final long OPT_BIT_TREAT_DYNAMIC_CALLS_AS_CONSTANT = 0x2L;
        private long optBits;

        private @Nullable RelBuilderFactory relBuilderFactory;
        private @Nullable java.lang.@org.checkerframework.checker.nullness.qual.Nullable String description;
        private @Nullable RelRule.OperandTransform operandSupplier;
        private boolean matchNullability;
        private boolean treatDynamicCallsAsConstant;

        private Builder() {
        }

        /**
         * Fill a builder with attribute values from the provided {@code org.apache.calcite.rel.rewriter.rules.MyReduceExpressionsRule.Config} instance.
         * @param instance The instance from which to copy values
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder from(MyReduceExpressionsRule.Config instance) {
            Objects.requireNonNull(instance, "instance");
            from((Object) instance);
            return this;
        }

        /**
         * Fill a builder with attribute values from the provided {@code org.apache.calcite.plan.RelRule.Config} instance.
         * @param instance The instance from which to copy values
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder from(RelRule.Config instance) {
            Objects.requireNonNull(instance, "instance");
            from((Object) instance);
            return this;
        }

        /**
         * Fill a builder with attribute values from the provided {@code org.apache.calcite.rel.rewriter.rules.MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig} instance.
         * @param instance The instance from which to copy values
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder from(MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig instance) {
            Objects.requireNonNull(instance, "instance");
            from((Object) instance);
            return this;
        }

        private void from(Object object) {
            if (object instanceof MyReduceExpressionsRule.Config) {
                MyReduceExpressionsRule.Config instance = (MyReduceExpressionsRule.Config) object;
                withTreatDynamicCallsAsConstant(instance.treatDynamicCallsAsConstant());
                withMatchNullability(instance.matchNullability());
            }
            if (object instanceof RelRule.Config) {
                RelRule.Config instance = (RelRule.Config) object;
                withRelBuilderFactory(instance.relBuilderFactory());
                withOperandSupplier(instance.operandSupplier());
                @Nullable java.lang.@org.checkerframework.checker.nullness.qual.Nullable String descriptionValue = instance.description();
                if (descriptionValue != null) {
                    withDescription(descriptionValue);
                }
            }
        }

        /**
         * Initializes the value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#relBuilderFactory() relBuilderFactory} attribute.
         * <p><em>If not set, this attribute will have a default value as returned by the initializer of {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#relBuilderFactory() relBuilderFactory}.</em>
         * @param relBuilderFactory The value for relBuilderFactory
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder withRelBuilderFactory(RelBuilderFactory relBuilderFactory) {
            this.relBuilderFactory = Objects.requireNonNull(relBuilderFactory, "relBuilderFactory");
            return this;
        }

        /**
         * Initializes the value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#description() description} attribute.
         * @param description The value for description (can be {@code null})
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder withDescription(@Nullable java.lang.@org.checkerframework.checker.nullness.qual.Nullable String description) {
            this.description = description;
            return this;
        }

        /**
         * Initializes the value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#operandSupplier() operandSupplier} attribute.
         * <p><em>If not set, this attribute will have a default value as returned by the initializer of {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#operandSupplier() operandSupplier}.</em>
         * @param operandSupplier The value for operandSupplier
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder withOperandSupplier(RelRule.OperandTransform operandSupplier) {
            this.operandSupplier = Objects.requireNonNull(operandSupplier, "operandSupplier");
            return this;
        }

        /**
         * Initializes the value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#matchNullability() matchNullability} attribute.
         * <p><em>If not set, this attribute will have a default value as returned by the initializer of {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#matchNullability() matchNullability}.</em>
         * @param matchNullability The value for matchNullability
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder withMatchNullability(boolean matchNullability) {
            this.matchNullability = matchNullability;
            optBits |= OPT_BIT_MATCH_NULLABILITY;
            return this;
        }

        /**
         * Initializes the value for the {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#treatDynamicCallsAsConstant() treatDynamicCallsAsConstant} attribute.
         * <p><em>If not set, this attribute will have a default value as returned by the initializer of {@link MyReduceExpressionsRule.MyJoinReduceExpressionsRule.MyJoinReduceExpressionsRuleConfig#treatDynamicCallsAsConstant() treatDynamicCallsAsConstant}.</em>
         * @param treatDynamicCallsAsConstant The value for treatDynamicCallsAsConstant
         * @return {@code this} builder for use in a chained invocation
         */
        @CanIgnoreReturnValue
        public final Builder withTreatDynamicCallsAsConstant(boolean treatDynamicCallsAsConstant) {
            this.treatDynamicCallsAsConstant = treatDynamicCallsAsConstant;
            optBits |= OPT_BIT_TREAT_DYNAMIC_CALLS_AS_CONSTANT;
            return this;
        }

        /**
         * Builds a new {@link ImmutableMyJoinReduceExpressionsRuleConfig ImmutableMyJoinReduceExpressionsRuleConfig}.
         * @return An immutable instance of MyJoinReduceExpressionsRuleConfig
         * @throws java.lang.IllegalStateException if any required attributes are missing
         */
        public ImmutableMyJoinReduceExpressionsRuleConfig build() {
            return ImmutableMyJoinReduceExpressionsRuleConfig.validate(new ImmutableMyJoinReduceExpressionsRuleConfig(this));
        }

        private boolean matchNullabilityIsSet() {
            return (optBits & OPT_BIT_MATCH_NULLABILITY) != 0;
        }

        private boolean treatDynamicCallsAsConstantIsSet() {
            return (optBits & OPT_BIT_TREAT_DYNAMIC_CALLS_AS_CONSTANT) != 0;
        }
    }
}
