#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PoseidonCameraDirector.generated.h"

class AAvehicleActor;
class UCameraComponent;
class APlayerController;

/**
 * EPoseidonCameraPreset - which camera view is active.
 *
 * Per SYSTEM_DESIGN.md Section 18.1 (Yonatan deliverable):
 *   1 - Chase camera - follows AUV at 10 m offset.
 *   2 - Top-down     - orthographic, shows SSV + AUV + drop in one frame.
 *   3 - Drop cine    - triggered by /coupling/drop_cmd, dolly-in.
 */
UENUM(BlueprintType)
enum class EPoseidonCameraPreset : uint8
{
    Chase         UMETA(DisplayName = "Chase (follow AUV)"),
    TopDown       UMETA(DisplayName = "Top-down (orthographic overview)"),
    DropCinematic UMETA(DisplayName = "Drop cinematic (dolly-in on release)")
};

/**
 * APoseidonCameraDirector - chooses which camera actor the player controller
 * views. Listens for the 1 / 2 / 3 action mappings defined in DefaultInput.ini
 * and listens for /coupling/drop_cmd on the rosbridge to auto-switch to the
 * drop cinematic.
 *
 * Place one instance in the level. It finds tagged AUV / SSV actors and the
 * three child camera components at BeginPlay.
 */
UCLASS(Blueprintable, BlueprintType)
class POSEIDONUE_API APoseidonCameraDirector : public AActor
{
    GENERATED_BODY()

public:
    APoseidonCameraDirector();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Activate a given preset. Can be called from Blueprints, console, or keybindings. */
    UFUNCTION(BlueprintCallable, Category = "Poseidon|Camera")
    void SetPreset(EPoseidonCameraPreset NewPreset);

    UFUNCTION() void ActivateChase()         { SetPreset(EPoseidonCameraPreset::Chase); }
    UFUNCTION() void ActivateTopDown()       { SetPreset(EPoseidonCameraPreset::TopDown); }
    UFUNCTION() void ActivateDropCinematic() { SetPreset(EPoseidonCameraPreset::DropCinematic); }

    /** Chase-camera offset from AUV, in meters (scaled by WorldScale internally). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Poseidon|Camera")
    FVector ChaseOffsetMeters = FVector(-10.f, 0.f, 3.f);

    /** Top-down altitude in meters above the midpoint of AUV and SSV. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Poseidon|Camera")
    float TopDownAltitudeMeters = 250.f;

    /** Drop-cinematic duration seconds after /coupling/drop_cmd. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Poseidon|Camera")
    float DropCinematicDurationSeconds = 6.f;

    /** Conversion from scenario meters to UE centimeters. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Poseidon|Camera")
    float WorldScale = 100.f;

private:
    UFUNCTION()
    void HandleBridgeMessage(const FString& JsonPayload);

    void BindInputActions();
    void UpdateChase(float DeltaSeconds);
    void UpdateTopDown(float DeltaSeconds);
    void UpdateDropCinematic(float DeltaSeconds);

    UPROPERTY()
    TObjectPtr<UCameraComponent> ChaseCamera = nullptr;

    UPROPERTY()
    TObjectPtr<UCameraComponent> TopDownCamera = nullptr;

    UPROPERTY()
    TObjectPtr<UCameraComponent> DropCamera = nullptr;

    UPROPERTY()
    TObjectPtr<AActor> AuvActor = nullptr;

    UPROPERTY()
    TObjectPtr<AActor> SsvActor = nullptr;

    UPROPERTY()
    TObjectPtr<APlayerController> PC = nullptr;

    EPoseidonCameraPreset CurrentPreset = EPoseidonCameraPreset::Chase;
    float DropElapsedSeconds = 0.f;
    FVector DropAnchor = FVector::ZeroVector;
};
