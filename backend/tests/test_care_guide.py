"""Tests for the pet care guide module - TDD approach."""

from care_guide import (
    CareTaskType,
    LifeStage,
    PetSpecies,
    get_cleaning_instructions,
    get_dusting_instructions,
    get_feeding_instructions,
    get_task_description,
    get_water_instructions,
)


class TestFeedingInstructions:
    """Test feeding instruction generation."""

    def test_adult_bearded_dragon_insect_feeding(self):
        """Adult bearded dragons get specific roach instructions."""
        instructions = get_feeding_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT, task_subtype="insects"
        )

        assert "3-5 adult Dubia roaches" in instructions
        assert "1 inch" in instructions or '1"' in instructions
        assert "calcium" in instructions.lower()
        assert "tongs" in instructions.lower() or "feed" in instructions.lower()

    def test_juvenile_bearded_dragon_insect_feeding(self):
        """Juvenile bearded dragons need more frequent feeding with smaller roaches."""
        instructions = get_feeding_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.JUVENILE, task_subtype="insects"
        )

        assert "medium" in instructions.lower() or "1/2" in instructions
        assert "calcium" in instructions.lower()
        # Juveniles need more insects
        assert any(num in instructions for num in ["10", "15", "20", "25"])

    def test_adult_bearded_dragon_greens_feeding(self):
        """Adult bearded dragons need daily greens."""
        instructions = get_feeding_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT, task_subtype="greens"
        )

        assert "collard" in instructions.lower() or "dandelion" in instructions.lower()
        assert "head" in instructions.lower()  # Size reference
        # Should mention what NOT to feed
        assert "spinach" in instructions.lower() or "avoid" in instructions.lower()

    def test_feeding_instructions_are_kid_friendly(self):
        """Instructions should be easy for 11-13 year olds to follow."""
        instructions = get_feeding_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT, task_subtype="insects"
        )

        # Should have numbered steps or clear structure
        assert "1." in instructions or "Step" in instructions or "•" in instructions
        # Should be reasonably concise
        assert len(instructions) < 1000


class TestWaterInstructions:
    """Test water change instruction generation."""

    def test_bearded_dragon_water_change(self):
        """Water change instructions should be specific."""
        instructions = get_water_instructions(species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT)

        assert "empty" in instructions.lower() or "dump" in instructions.lower()
        assert "fresh" in instructions.lower()
        assert "rinse" in instructions.lower() or "clean" in instructions.lower()

    def test_water_instructions_mention_water_type(self):
        """Should specify what kind of water to use."""
        instructions = get_water_instructions(species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT)

        # Should mention filtered or dechlorinated water
        water_types = ["filtered", "dechlorinated", "bottled", "tap"]
        assert any(wt in instructions.lower() for wt in water_types)


class TestCleaningInstructions:
    """Test tank cleaning instruction generation."""

    def test_spot_cleaning_instructions(self):
        """Spot cleaning should have specific instructions."""
        instructions = get_cleaning_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT, task_subtype="spot_clean"
        )

        assert "food" in instructions.lower()  # Remove uneaten food
        assert "paper towel" in instructions.lower() or "scoop" in instructions.lower()
        assert "weekly" in instructions.lower()  # Should mention poop is done weekly

    def test_deep_cleaning_instructions(self):
        """Deep cleaning should be more thorough and include poop removal."""
        instructions = get_cleaning_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT, task_subtype="deep_clean"
        )

        assert "poop" in instructions.lower()  # Poop removal is part of weekly deep clean
        assert "decor" in instructions.lower() or "decorations" in instructions.lower()
        assert "wipe" in instructions.lower() or "scrub" in instructions.lower()
        assert "walls" in instructions.lower()


class TestDustingInstructions:
    """Test calcium/vitamin dusting instruction generation."""

    def test_calcium_dusting_instructions(self):
        """Calcium dusting should have clear instructions."""
        instructions = get_dusting_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT, task_subtype="calcium"
        )

        assert "calcium" in instructions.lower()
        assert "shake" in instructions.lower() or "dust" in instructions.lower()
        assert "light" in instructions.lower() or "thin" in instructions.lower()  # Light coating

    def test_multivitamin_dusting_instructions(self):
        """Multivitamin dusting instructions."""
        instructions = get_dusting_instructions(
            species=PetSpecies.BEARDED_DRAGON, life_stage=LifeStage.ADULT, task_subtype="multivitamin"
        )

        assert "vitamin" in instructions.lower() or "multivitamin" in instructions.lower()
        assert "2" in instructions or "twice" in instructions.lower()  # 2x per week


class TestGetTaskDescription:
    """Test the main task description generator."""

    def test_generates_feeding_description(self):
        """Should generate appropriate feeding description."""
        description = get_task_description(
            task_type=CareTaskType.FEEDING,
            species=PetSpecies.BEARDED_DRAGON,
            life_stage=LifeStage.ADULT,
            task_name="Morning Feeding",
        )

        assert description is not None
        assert len(description) > 50  # Should be detailed

    def test_generates_water_description(self):
        """Should generate water change description."""
        description = get_task_description(
            task_type=CareTaskType.WATER,
            species=PetSpecies.BEARDED_DRAGON,
            life_stage=LifeStage.ADULT,
            task_name="Change Water",
        )

        assert description is not None
        assert "water" in description.lower()

    def test_generates_cleaning_description(self):
        """Should generate cleaning description."""
        description = get_task_description(
            task_type=CareTaskType.CLEANING,
            species=PetSpecies.BEARDED_DRAGON,
            life_stage=LifeStage.ADULT,
            task_name="Spot Clean Tank",
        )

        assert description is not None
        assert "clean" in description.lower()

    def test_unknown_species_returns_generic(self):
        """Unknown species should return generic but helpful instructions."""
        description = get_task_description(
            task_type=CareTaskType.FEEDING, species="unknown_pet", life_stage=LifeStage.ADULT, task_name="Feed Pet"
        )

        assert description is not None
        assert len(description) > 20


class TestTaskTypeDetection:
    """Test automatic detection of task subtypes from task names."""

    def test_detects_insect_feeding_from_name(self):
        """Should detect insect feeding from task name."""
        description = get_task_description(
            task_type=CareTaskType.FEEDING,
            species=PetSpecies.BEARDED_DRAGON,
            life_stage=LifeStage.ADULT,
            task_name="Feed Dubia Roaches",
        )

        assert "roach" in description.lower() or "dubia" in description.lower()

    def test_detects_greens_feeding_from_name(self):
        """Should detect greens feeding from task name."""
        description = get_task_description(
            task_type=CareTaskType.FEEDING,
            species=PetSpecies.BEARDED_DRAGON,
            life_stage=LifeStage.ADULT,
            task_name="Feed Greens/Salad",
        )

        assert "green" in description.lower() or "salad" in description.lower() or "vegetable" in description.lower()

    def test_detects_spot_clean_from_name(self):
        """Should detect spot cleaning from task name."""
        description = get_task_description(
            task_type=CareTaskType.CLEANING,
            species=PetSpecies.BEARDED_DRAGON,
            life_stage=LifeStage.ADULT,
            task_name="Daily Spot Clean",
        )

        assert "food" in description.lower()  # Remove uneaten food
        assert "spot" in description.lower() or "daily" in description.lower()
